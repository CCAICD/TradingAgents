"""Tencent Finance data provider for A-stock market data.

This provider uses Tencent Finance APIs to fetch:
- valuation: PE, PB ratios
- market_cap: Market capitalization
- turnover_rate: Turnover rate
- limit_price: Price limits (涨停/跌停价)

Status: EXPERIMENTAL v0.1

Limitations:
- Supplementary source only, not primary market data
- Field indices verified from limited smoke tests
- Batch query not verified
- Beijing Exchange not verified
- empty/failed only degrades supplementary fields, not primary market data
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

# Tencent endpoint configuration
TENCENT_ENDPOINT_TEMPLATE = "https://qt.gtimg.cn/q={symbol}"

# Default headers
_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
}

# Known field indices (from smoke test validation)
_FIELD_INDICES = {
    "name": 1,
    "code": 2,
    "current_price": 3,
    "yesterday_close": 4,
    "today_open": 5,
    "volume": 6,
    "change_amount": 31,
    "change_percent": 32,
    "highest": 33,
    "lowest": 34,
    "turnover_rate": 38,
    "pe_ratio": 39,
    "circulating_market_cap": 44,
    "total_market_cap": 45,
    "pb_ratio": 46,
    "limit_up_price": 47,
    "limit_down_price": 48,
}

# Minimum fields required for a valid response
_MIN_FIELDS = 49


def _convert_to_tencent_symbol(ticker: str) -> tuple:
    """Convert ticker to Tencent symbol format.

    Args:
        ticker: Stock ticker (e.g., "600519.SH", "000001.SZ", "sh600519")

    Returns:
        Tuple of (tencent_symbol, warning_message)
    """
    if not ticker:
        return None, "ticker is required"

    ticker = ticker.strip().upper()

    # Remove suffix if present
    if "." in ticker:
        code, suffix = ticker.split(".", 1)
        if suffix == "SH":
            return f"sh{code}", None
        elif suffix == "SZ":
            return f"sz{code}", None
        else:
            return f"sh{code}", f"Unknown suffix {suffix}, defaulting to sh"

    # Check if already has prefix
    if ticker.startswith("SH"):
        return ticker.lower(), None
    elif ticker.startswith("SZ"):
        return ticker.lower(), None

    # Infer from code
    code = ticker
    if code.startswith(("600", "601", "603", "605", "688", "689")):
        return f"sh{code}", None
    elif code.startswith(("000", "001", "002", "003", "300", "301")):
        return f"sz{code}", None
    elif code.startswith(("8", "4")):
        return f"bj{code}", "Beijing exchange symbol format is unverified for tencent provider"
    else:
        return f"sh{code}", f"Cannot infer market from {code}, defaulting to sh"


def _parse_float(value: str) -> tuple:
    """Parse float value from string.

    Returns:
        Tuple of (value, warning_message)
    """
    if not value or value.strip() == "":
        return None, "empty value"

    try:
        return float(value.strip()), None
    except ValueError:
        return None, f"failed to parse '{value}' as float"


def _parse_tencent_response(content: str, dataset: str) -> Dict[str, Any]:
    """Parse Tencent response and extract fields.

    Args:
        content: Response content
        dataset: Requested dataset

    Returns:
        Dict with parsed data and metadata
    """
    warnings = []

    # Check for empty response
    if not content or content.strip() == "":
        return {
            "status": ProviderStatus.EMPTY,
            "data": None,
            "warnings": ["empty tencent result should be treated as missing supplementary data"],
        }

    # Extract payload between quotes
    if "=" not in content:
        return {
            "status": ProviderStatus.FAILED,
            "data": None,
            "warnings": ["Response format invalid: no '=' found"],
        }

    _, _, value_part = content.partition("=")
    value_part = value_part.strip().strip('"').strip(";").strip('"')

    if not value_part:
        return {
            "status": ProviderStatus.EMPTY,
            "data": None,
            "warnings": ["empty tencent result should be treated as missing supplementary data"],
        }

    # Split by ~
    fields = value_part.split("~")

    # Check minimum fields
    if len(fields) < _MIN_FIELDS:
        return {
            "status": ProviderStatus.FAILED,
            "data": None,
            "warnings": [f"Field count {len(fields)} < {_MIN_FIELDS}"],
            "field_count": len(fields),
        }

    # Parse common fields
    result = {
        "ticker": fields[_FIELD_INDICES["code"]] if len(fields) > _FIELD_INDICES["code"] else None,
        "name": fields[_FIELD_INDICES["name"]] if len(fields) > _FIELD_INDICES["name"] else None,
        "source": "tencent",
        "raw_field_count": len(fields),
        "raw_field_indices": _FIELD_INDICES,
    }

    # Parse dataset-specific fields
    if dataset == "valuation":
        pe_ratio, pe_warning = _parse_float(fields[_FIELD_INDICES["pe_ratio"]])
        pb_ratio, pb_warning = _parse_float(fields[_FIELD_INDICES["pb_ratio"]])

        result["pe_ratio"] = pe_ratio
        result["pb_ratio"] = pb_ratio

        if pe_warning:
            warnings.append(f"pe_ratio: {pe_warning}")
        if pb_warning:
            warnings.append(f"pb_ratio: {pb_warning}")

    elif dataset == "market_cap":
        circ_cap, circ_warning = _parse_float(fields[_FIELD_INDICES["circulating_market_cap"]])
        total_cap, total_warning = _parse_float(fields[_FIELD_INDICES["total_market_cap"]])

        result["circulating_market_cap"] = circ_cap
        result["total_market_cap"] = total_cap
        result["unit"] = "亿元"
        result["unit_unverified"] = True

        if circ_warning:
            warnings.append(f"circulating_market_cap: {circ_warning}")
        if total_warning:
            warnings.append(f"total_market_cap: {total_warning}")

    elif dataset == "turnover_rate":
        turnover, turnover_warning = _parse_float(fields[_FIELD_INDICES["turnover_rate"]])

        result["turnover_rate"] = turnover

        if turnover_warning:
            warnings.append(f"turnover_rate: {turnover_warning}")

    elif dataset == "limit_price":
        limit_up, up_warning = _parse_float(fields[_FIELD_INDICES["limit_up_price"]])
        limit_down, down_warning = _parse_float(fields[_FIELD_INDICES["limit_down_price"]])

        result["limit_up_price"] = limit_up
        result["limit_down_price"] = limit_down

        if up_warning:
            warnings.append(f"limit_up_price: {up_warning}")
        if down_warning:
            warnings.append(f"limit_down_price: {down_warning}")

    # Determine status
    dataset_fields = {
        "valuation": ["pe_ratio", "pb_ratio"],
        "market_cap": ["circulating_market_cap", "total_market_cap"],
        "turnover_rate": ["turnover_rate"],
        "limit_price": ["limit_up_price", "limit_down_price"],
    }

    required_fields = dataset_fields.get(dataset, [])
    missing_fields = [f for f in required_fields if result.get(f) is None]

    if missing_fields:
        status = ProviderStatus.PARTIAL
        warnings.append(f"Missing fields: {', '.join(missing_fields)}")
    else:
        status = ProviderStatus.SUCCESS

    return {
        "status": status,
        "data": result,
        "warnings": warnings,
    }


class TencentProvider(BaseCnStockProvider):
    """Provider for A-stock data via Tencent Finance.

    Status: EXPERIMENTAL v0.1

    Tencent Finance provides valuation, market cap, turnover rate,
    and price limit data.

    Important:
    - This is a supplementary source, not primary market data
    - empty/failed only degrades supplementary fields
    - Does not block primary market data conclusions
    """

    def __init__(
        self,
        raw_store: Optional[RawPayloadStore] = None,
        rate_limit_config: Optional[ProviderRateLimitConfig] = None,
    ):
        """Initialize TencentProvider.

        Args:
            raw_store: RawPayloadStore for saving raw payloads
            rate_limit_config: Rate limit configuration
        """
        self._raw_store = raw_store or RawPayloadStore()
        self._rate_limit_config = rate_limit_config or ProviderRateLimitConfig(
            min_interval_seconds=0.5,
            jitter_seconds=0.2,
        )
        self._limiter = RateLimiter(config=self._rate_limit_config)

    @property
    def provider_name(self) -> str:
        return "tencent"

    @property
    def supported_datasets(self) -> List[str]:
        return ["valuation", "market_cap", "turnover_rate", "limit_price"]

    def fetch(self, dataset_name: str, **kwargs) -> ProviderResult:
        """Fetch data from Tencent Finance.

        Args:
            dataset_name: Name of the dataset to fetch
            **kwargs: Additional parameters:
                - ticker: Stock ticker (required)
                - timeout: Request timeout (optional)

        Returns:
            ProviderResult with fetched data
        """
        now = datetime.now()

        # Rate limiting
        self._limiter.wait()

        try:
            if dataset_name not in self.supported_datasets:
                return ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name=dataset_name,
                    status=ProviderStatus.NOT_IMPLEMENTED,
                    fetched_at=now,
                    error_message=f"Unsupported dataset: {dataset_name}",
                )

            return self._fetch_data(dataset_name, now, **kwargs)

        except Exception as e:
            logger.error(f"Tencent fetch failed for {dataset_name}: {e}")
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name=dataset_name,
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"Fetch failed: {e}",
            )
        finally:
            self._limiter.record_call()

    def _fetch_data(self, dataset_name: str, now: datetime, **kwargs) -> ProviderResult:
        """Fetch data from Tencent Finance."""
        import requests

        ticker = kwargs.get("ticker")
        timeout = kwargs.get("timeout", 15)

        warnings = []

        # Validate ticker
        if not ticker:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name=dataset_name,
                source="tencent",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message="ticker is required",
                metadata={"experimental": True, "supplementary_source": True},
            )

        # Convert to Tencent symbol format
        tencent_symbol, symbol_warning = _convert_to_tencent_symbol(ticker)
        if symbol_warning:
            warnings.append(symbol_warning)

        if not tencent_symbol:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name=dataset_name,
                source="tencent",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message="Failed to convert ticker to Tencent format",
                metadata={"experimental": True, "supplementary_source": True},
            )

        # Build URL
        url = TENCENT_ENDPOINT_TEMPLATE.format(symbol=tencent_symbol)

        try:
            # Make request
            response = requests.get(
                url,
                headers=_DEFAULT_HEADERS,
                timeout=timeout,
            )

            # Check HTTP status
            if response.status_code != 200:
                return ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name=dataset_name,
                    source="tencent",
                    status=ProviderStatus.FAILED,
                    fetched_at=now,
                    error_message=f"HTTP {response.status_code}",
                    metadata={"experimental": True, "supplementary_source": True},
                )

            # Decode response
            content_type = response.headers.get("Content-Type", "")
            if "charset" in content_type.lower():
                try:
                    content = response.text
                except Exception:
                    content = response.content.decode("gbk", errors="replace")
                    warnings.append("Used GBK fallback for decoding")
            else:
                try:
                    content = response.content.decode("gbk")
                except UnicodeDecodeError:
                    try:
                        content = response.content.decode("gb2312")
                    except UnicodeDecodeError:
                        content = response.content.decode("utf-8", errors="replace")
                        warnings.append("Used UTF-8 fallback for decoding")

            # Parse response
            parse_result = _parse_tencent_response(content, dataset_name)

            if parse_result["status"] in (ProviderStatus.FAILED, ProviderStatus.EMPTY):
                return ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name=dataset_name,
                    source="tencent",
                    status=parse_result["status"],
                    fetched_at=now,
                    data=content,
                    warnings=[*warnings, *parse_result.get("warnings", [])],
                    metadata={
                        "experimental": True,
                        "supplementary_source": True,
                        "tencent_symbol": tencent_symbol,
                    },
                )

            # Success or partial
            parsed_data = parse_result["data"]

            # Save raw payload
            raw_path = self._raw_store.save(
                provider_name=self.provider_name,
                dataset_name=dataset_name,
                data=content,
                symbol=ticker,
                file_format="text",
            )

            # as_of_time warning
            as_of_time = None
            warnings.append("as_of_time unverified for tencent provider")

            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name=dataset_name,
                source="tencent",
                status=parse_result["status"],
                fetched_at=now,
                as_of_time=as_of_time,
                data=content,
                normalized_data=parsed_data,
                raw_payload_path=str(raw_path),
                warnings=[*warnings, *parse_result.get("warnings", [])],
                metadata={
                    "experimental": True,
                    "supplementary_source": True,
                    "tencent_symbol": tencent_symbol,
                    "unit_unverified": parsed_data.get("unit_unverified", False),
                },
            )

        except requests.exceptions.Timeout:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name=dataset_name,
                source="tencent",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"Request timeout after {timeout}s",
                metadata={"experimental": True, "supplementary_source": True},
            )
        except requests.exceptions.ConnectionError as e:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name=dataset_name,
                source="tencent",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"Connection error: {e}",
                metadata={"experimental": True, "supplementary_source": True},
            )
