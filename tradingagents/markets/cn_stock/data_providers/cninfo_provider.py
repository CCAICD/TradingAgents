"""Cninfo (巨潮) data provider for A-stock announcement data.

This provider uses Cninfo APIs to fetch:
- announcement: Company announcements (公告)

Status: EXPERIMENTAL v0.1

Limitations:
- No PDF download
- No risk level evaluation
- No Disclosure Guard integration
- Empty/failed results must NOT be interpreted as "no major negative"
- GBK encoding required
- orgId format required for stock parameter
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseCnStockProvider
from .raw_store import RawPayloadStore
from .rate_limiter import ProviderRateLimitConfig, RateLimiter
from .schema import ProviderResult, ProviderStatus

logger = logging.getLogger(__name__)

# Cninfo endpoint configuration
CNINFO_ENDPOINT = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
CNINFO_PDF_BASE = "https://static.cninfo.com.cn/"

# Known orgId prefixes
_ORGID_PREFIXES = {
    "000": "gssz",  # 深市主板
    "001": "gssz",  # 深市主板
    "002": "gssz",  # 深市中小板
    "003": "gssz",  # 深市创业板
    "300": "gssz",  # 深市创业板
    "301": "gssz",  # 深市创业板
    "600": "gssh",  # 沪市主板
    "601": "gssh",  # 沪市主板
    "603": "gssh",  # 沪市主板
    "605": "gssh",  # 沪市主板
    "688": "gssh",  # 沪市科创板
    "689": "gssh",  # 沪市科创板
}

# Default headers for Cninfo requests
_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://www.cninfo.com.cn/new/disclosure",
    "Origin": "https://www.cninfo.com.cn",
}


def _infer_org_id(ticker: str) -> Optional[str]:
    """Infer orgId from ticker code.

    Args:
        ticker: Stock ticker (e.g., "000001", "600519")

    Returns:
        orgId string or None if cannot infer
    """
    if not ticker or len(ticker) < 6:
        return None

    prefix = ticker[:3]
    org_prefix = _ORGID_PREFIXES.get(prefix)

    if org_prefix:
        # Format: prefix + ticker (6 digits)
        return f"{org_prefix}{ticker}"

    return None


def _parse_announcement_time(time_ms: Optional[int]) -> tuple:
    """Parse announcementTime from milliseconds to datetime.

    Args:
        time_ms: Timestamp in milliseconds

    Returns:
        Tuple of (datetime, warning_message)
    """
    if time_ms is None:
        return None, "announcementTime is None"

    try:
        # Convert milliseconds to seconds
        time_s = time_ms / 1000
        dt = datetime.fromtimestamp(time_s)
        return dt, None
    except (ValueError, OSError, OverflowError) as e:
        return None, f"Failed to parse announcementTime {time_ms}: {e}"


def _build_pdf_url(adjunct_url: Optional[str]) -> Optional[str]:
    """Build full PDF URL from adjunctUrl.

    Args:
        adjunct_url: Relative URL from Cninfo response

    Returns:
        Full PDF URL or None
    """
    if not adjunct_url:
        return None

    # Remove leading slash if present
    adjunct_url = adjunct_url.lstrip("/")

    return f"{CNINFO_PDF_BASE}{adjunct_url}"


def _normalize_announcement(item: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a single announcement item.

    Args:
        item: Raw announcement dict from Cninfo

    Returns:
        Normalized announcement dict
    """
    warnings = []

    # Parse announcement time
    publish_time, time_warning = _parse_announcement_time(item.get("announcementTime"))
    if time_warning:
        warnings.append(time_warning)

    # Build PDF URL
    pdf_url = _build_pdf_url(item.get("adjunctUrl"))
    if not pdf_url and item.get("adjunctUrl"):
        warnings.append("Failed to build PDF URL")

    # Check for missing fields
    if not item.get("announcementId"):
        warnings.append("Missing announcementId")
    if not item.get("announcementTitle"):
        warnings.append("Missing announcementTitle")
    if not item.get("secCode"):
        warnings.append("Missing secCode")

    return {
        "announcement_id": item.get("announcementId"),
        "announcement_title": item.get("announcementTitle", ""),
        "announcement_time_raw": item.get("announcementTime"),
        "publish_time": publish_time.isoformat() if publish_time else None,
        "ticker": item.get("secCode", ""),
        "name": item.get("secName", ""),
        "org_id": item.get("orgId", ""),
        "adjunct_url": item.get("adjunctUrl"),
        "adjunct_size": item.get("adjunctSize"),
        "adjunct_type": item.get("adjunctType"),
        "column_id": item.get("columnId"),
        "announcement_type": item.get("announcementType"),
        "pdf_url": pdf_url,
        "source": "cninfo",
        "risk_level_candidate": "not_evaluated",
        "matched_keywords": [],
        "warnings": warnings,
    }


class CninfoProvider(BaseCnStockProvider):
    """Provider for A-stock announcement data via Cninfo (巨潮资讯).

    Status: EXPERIMENTAL v0.1

    Cninfo provides official company announcements for A-stock market.

    Important:
    - This is an experimental provider
    - No PDF download
    - No risk level evaluation
    - Empty/failed results must NOT be interpreted as "no major negative"
    - Announcement failure means report cannot claim "no major negative"
    """

    def __init__(
        self,
        raw_store: Optional[RawPayloadStore] = None,
        rate_limit_config: Optional[ProviderRateLimitConfig] = None,
    ):
        """Initialize CninfoProvider.

        Args:
            raw_store: RawPayloadStore for saving raw payloads
            rate_limit_config: Rate limit configuration
        """
        self._raw_store = raw_store or RawPayloadStore()
        self._rate_limit_config = rate_limit_config or ProviderRateLimitConfig(
            min_interval_seconds=1.0,
            jitter_seconds=0.3,
        )
        self._limiter = RateLimiter(config=self._rate_limit_config)

    @property
    def provider_name(self) -> str:
        return "cninfo"

    @property
    def supported_datasets(self) -> List[str]:
        return ["announcement"]

    def fetch(self, dataset_name: str, **kwargs) -> ProviderResult:
        """Fetch announcement data from Cninfo.

        Args:
            dataset_name: Must be "announcement"
            **kwargs: Additional parameters:
                - ticker: Stock ticker (optional)
                - org_id: Organization ID (optional)
                - start_date: Start date YYYY-MM-DD (optional)
                - end_date: End date YYYY-MM-DD (optional)
                - page: Page number (default: 1)
                - page_size: Results per page (default: 5, max: 30)
                - category: Announcement category (optional)
                - column: Column (optional)
                - plate: Plate (optional)
                - search_key: Search keyword (optional)
                - timeout: Request timeout (optional)

        Returns:
            ProviderResult with announcement data
        """
        now = datetime.now()

        # Rate limiting
        self._limiter.wait()

        try:
            if dataset_name != "announcement":
                return ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name=dataset_name,
                    status=ProviderStatus.NOT_IMPLEMENTED,
                    fetched_at=now,
                    error_message=f"Unsupported dataset: {dataset_name}",
                )

            return self._fetch_announcement(now, **kwargs)

        except Exception as e:
            logger.error(f"Cninfo fetch failed for {dataset_name}: {e}")
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name=dataset_name,
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"Fetch failed: {e}",
            )
        finally:
            self._limiter.record_call()

    def _fetch_announcement(self, now: datetime, **kwargs) -> ProviderResult:
        """Fetch announcement data."""
        import requests

        # Extract parameters
        ticker = kwargs.get("ticker")
        org_id = kwargs.get("org_id")
        start_date = kwargs.get("start_date")
        end_date = kwargs.get("end_date")
        page = kwargs.get("page", 1)
        page_size = kwargs.get("page_size", 5)
        category = kwargs.get("category")
        column = kwargs.get("column")
        plate = kwargs.get("plate")
        search_key = kwargs.get("search_key")
        timeout = kwargs.get("timeout", 15)

        warnings = []

        # Validate page_size
        if page_size > 30:
            warnings.append(f"page_size {page_size} truncated to 30")
            page_size = 30

        # Build stock parameter
        stock_param = None
        if ticker:
            if org_id:
                stock_param = f"{ticker},{org_id}"
            else:
                # Try to infer org_id
                inferred_org_id = _infer_org_id(ticker)
                if inferred_org_id:
                    stock_param = f"{ticker},{inferred_org_id}"
                    warnings.append(f"Inferred org_id: {inferred_org_id}")
                else:
                    stock_param = ticker
                    warnings.append(f"Could not infer org_id for {ticker}")

        # Build form data
        form_data = {
            "pageNum": str(page),
            "pageSize": str(page_size),
            "tabName": "fulltext",
        }

        if stock_param:
            form_data["stock"] = stock_param
        if column:
            form_data["column"] = column
        else:
            form_data["column"] = "szse"  # Default to Shenzhen
        if category:
            form_data["category"] = category
        if plate:
            form_data["plate"] = plate
        if search_key:
            form_data["searchkey"] = search_key

        # Build date range
        if start_date and end_date:
            form_data["seDate"] = f"{start_date}~{end_date}"
        elif start_date:
            form_data["seDate"] = f"{start_date}~"
        elif end_date:
            form_data["seDate"] = f"~{end_date}"

        try:
            # Make request
            response = requests.post(
                CNINFO_ENDPOINT,
                data=form_data,
                headers=_DEFAULT_HEADERS,
                timeout=timeout,
            )

            # Check HTTP status
            if response.status_code != 200:
                return ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name="announcement",
                    source="cninfo",
                    status=ProviderStatus.FAILED,
                    fetched_at=now,
                    error_message=f"HTTP {response.status_code}",
                    metadata={"experimental": True, "no_pdf_download": True},
                )

            # Decode GBK
            try:
                content = response.content.decode("gbk")
            except UnicodeDecodeError:
                # Fallback to UTF-8
                content = response.content.decode("utf-8", errors="replace")
                warnings.append("GBK decode failed, using UTF-8 fallback")

            # Parse JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                return ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name="announcement",
                    source="cninfo",
                    status=ProviderStatus.FAILED,
                    fetched_at=now,
                    error_message=f"JSON parse failed: {e}",
                    metadata={"experimental": True, "no_pdf_download": True},
                )

            # Check response structure
            if not isinstance(data, dict):
                return ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name="announcement",
                    source="cninfo",
                    status=ProviderStatus.FAILED,
                    fetched_at=now,
                    error_message="Response is not a dict",
                    metadata={"experimental": True, "no_pdf_download": True},
                )

            # Extract announcements
            announcements = data.get("announcements")
            total_announcement = data.get("totalAnnouncement", 0)
            has_more = data.get("hasMore", False)

            # Handle empty announcements
            if not announcements or len(announcements) == 0:
                return ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name="announcement",
                    source="cninfo",
                    status=ProviderStatus.EMPTY,
                    fetched_at=now,
                    warnings=[
                        "Empty announcement result must not be interpreted as no major negative event",
                        *warnings,
                    ],
                    metadata={
                        "experimental": True,
                        "no_pdf_download": True,
                        "total_announcement": total_announcement,
                        "has_more": has_more,
                    },
                )

            # Normalize announcements
            normalized = [_normalize_announcement(item) for item in announcements]

            # Extract as_of_time from latest announcement
            as_of_time = None
            for ann in normalized:
                if ann.get("publish_time"):
                    try:
                        dt = datetime.fromisoformat(ann["publish_time"])
                        if as_of_time is None or dt > as_of_time:
                            as_of_time = dt
                    except ValueError:
                        pass

            if as_of_time is None:
                warnings.append("Could not extract as_of_time from announcements")

            # Save raw payload
            raw_path = self._raw_store.save(
                provider_name=self.provider_name,
                dataset_name="announcement",
                data=data,
                file_format="json",
            )

            # Check for partial status (missing fields)
            status = ProviderStatus.SUCCESS
            for ann in normalized:
                if ann.get("warnings"):
                    status = ProviderStatus.PARTIAL
                    warnings.extend(ann["warnings"])
                    break

            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="announcement",
                source="cninfo",
                status=status,
                fetched_at=now,
                as_of_time=as_of_time,
                data=data,
                normalized_data=normalized,
                raw_payload_path=str(raw_path),
                warnings=warnings,
                metadata={
                    "experimental": True,
                    "no_pdf_download": True,
                    "total_announcement": total_announcement,
                    "has_more": has_more,
                    "page": page,
                    "page_size": page_size,
                },
            )

        except requests.exceptions.Timeout:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="announcement",
                source="cninfo",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"Request timeout after {timeout}s",
                metadata={"experimental": True, "no_pdf_download": True},
            )
        except requests.exceptions.ConnectionError as e:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="announcement",
                source="cninfo",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"Connection error: {e}",
                metadata={"experimental": True, "no_pdf_download": True},
            )
