"""Provider result to DataStatus conversion.

This module provides helpers for converting ProviderResult to DataStatus
for integration with DataFreshnessGuard.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from tradingagents.markets.common.data_status import DataFreshStatus, DataStatus

from .schema import ProviderResult, ProviderStatus


def provider_result_to_data_status(
    result: ProviderResult,
    required: bool = False,
    max_age_seconds: Optional[int] = None,
) -> DataStatus:
    """Convert ProviderResult to DataStatus.

    Mapping:
    - SUCCESS → FRESH (if fetched_at is recent) or UNKNOWN
    - PARTIAL → PARTIAL
    - EMPTY → MISSING
    - FAILED → FAILED
    - SKIPPED → UNKNOWN
    - NOT_IMPLEMENTED → UNKNOWN

    Args:
        result: ProviderResult from a data provider
        required: Whether this dataset is required
        max_age_seconds: Optional freshness threshold

    Returns:
        DataStatus for DataFreshnessGuard
    """
    # Map status
    status_map = {
        ProviderStatus.SUCCESS: DataFreshStatus.FRESH,
        ProviderStatus.PARTIAL: DataFreshStatus.PARTIAL,
        ProviderStatus.EMPTY: DataFreshStatus.MISSING,
        ProviderStatus.FAILED: DataFreshStatus.FAILED,
        ProviderStatus.SKIPPED: DataFreshStatus.UNKNOWN,
        ProviderStatus.NOT_IMPLEMENTED: DataFreshStatus.UNKNOWN,
    }

    data_status = status_map.get(result.status, DataFreshStatus.UNKNOWN)

    # If success but no fetched_at, mark as unknown
    if result.status == ProviderStatus.SUCCESS and result.fetched_at is None:
        data_status = DataFreshStatus.UNKNOWN

    return DataStatus(
        dataset_name=result.dataset_name,
        market=result.market,
        source=result.source or result.provider_name,
        status=data_status,
        fetched_at=result.fetched_at,
        as_of_time=result.as_of_time,
        max_age_seconds=max_age_seconds,
        required=required,
        error_message=result.error_message,
        raw_payload_path=result.raw_payload_path,
        metadata=result.metadata,
    )
