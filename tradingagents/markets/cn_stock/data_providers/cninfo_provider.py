"""Cninfo (巨潮) data provider for A-stock announcement data.

This provider uses Cninfo APIs to fetch:
- announcement: Company announcements (公告)

NOTE: Cninfo API endpoints require validation.
This is a skeleton implementation - endpoints are not confirmed.

Limitations:
- API endpoints are not confirmed
- No default network calls
- Returns not_implemented until endpoints are validated
- Does not implement Disclosure Guard
- Does not implement Negative Event Guard
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseCnStockProvider
from .raw_store import RawPayloadStore
from .rate_limiter import ProviderRateLimitConfig, RateLimiter
from .schema import ProviderResult, ProviderStatus

logger = logging.getLogger(__name__)


class CninfoProvider(BaseCnStockProvider):
    """Provider for A-stock announcement data via Cninfo (巨潮资讯).

    Cninfo provides official company announcements for A-stock market.

    Requires:
    - requests package (for HTTP calls)
    - Valid API endpoints (not confirmed yet)

    NOTE: This is a skeleton implementation.
    Endpoints require validation before real data can be fetched.

    Important:
    - Announcement failure means report cannot claim "no major negative"
    - This provider does not implement Disclosure Guard
    - This provider does not implement Negative Event Guard
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

        NOTE: This is a skeleton implementation.
        Endpoints are not confirmed, so all datasets return not_implemented.

        Args:
            dataset_name: Name of the dataset to fetch
            **kwargs: Additional parameters:
                - ticker: Stock ticker (optional)
                - start_date: Start date (optional)
                - end_date: End date (optional)
                - market: Market (optional)
                - page: Page number (optional)
                - page_size: Page size (optional)
                - announcement_type: Announcement type (optional)

        Returns:
            ProviderResult with not_implemented status
        """
        now = datetime.now()

        # Rate limiting
        self._limiter.wait()

        try:
            if dataset_name not in self.supported_datasets:
                return ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name=dataset_name,
                    status=ProviderStatus.FAILED,
                    fetched_at=now,
                    error_message=f"Unsupported dataset: {dataset_name}",
                )

            # All endpoints return not_implemented until validated
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name=dataset_name,
                source="cninfo",
                status=ProviderStatus.NOT_IMPLEMENTED,
                fetched_at=now,
                error_message=(
                    f"Cninfo endpoint for {dataset_name} is not confirmed. "
                    "This is a skeleton implementation. "
                    "Endpoints require validation before real data can be fetched. "
                    "NOTE: Announcement failure means report cannot claim 'no major negative'."
                ),
                metadata={
                    "dataset": dataset_name,
                    "status": "skeleton",
                    "requires_validation": True,
                    "report_impact": "Announcement failure blocks 'no major negative' claim",
                    "ticker": kwargs.get("ticker"),
                    "start_date": kwargs.get("start_date"),
                    "end_date": kwargs.get("end_date"),
                },
            )

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
