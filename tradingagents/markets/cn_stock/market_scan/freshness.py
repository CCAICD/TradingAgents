"""Market-Wide Scan freshness helper.

This module provides helpers for building DataStatus objects
for Market-Wide Scan inputs and checking freshness via DataFreshnessGuard.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from tradingagents.markets.common.data_status import DataFreshStatus, DataStatus
from tradingagents.markets.common.data_freshness import DataFreshnessGuard


def build_market_scan_freshness_status(
    trade_date: str,
    scan_time: Optional[datetime] = None,
    has_index_data: bool = False,
    has_breadth_data: bool = False,
    has_turnover_data: bool = False,
    has_sector_data: bool = False,
    has_limit_up_pool: bool = False,
    has_strong_stocks: bool = False,
    has_attention_pool: bool = False,
    has_announcement: bool = False,
    index_fetched_at: Optional[datetime] = None,
    breadth_fetched_at: Optional[datetime] = None,
    turnover_fetched_at: Optional[datetime] = None,
    sector_fetched_at: Optional[datetime] = None,
    limit_up_fetched_at: Optional[datetime] = None,
) -> List[DataStatus]:
    """Build DataStatus list for Market-Wide Scan.

    Args:
        trade_date: Trade date
        scan_time: Scan time
        has_*: Whether data is available
        *_fetched_at: When data was fetched

    Returns:
        List of DataStatus objects
    """
    now = scan_time or datetime.now()
    statuses = []

    # Index data
    statuses.append(DataStatus(
        dataset_name="index_data",
        market="cn_stock",
        source="mootdx",
        status=DataFreshStatus.FRESH if has_index_data else DataFreshStatus.MISSING,
        fetched_at=index_fetched_at or (now if has_index_data else None),
        required=True,
    ))

    # Market breadth
    statuses.append(DataStatus(
        dataset_name="market_breadth",
        market="cn_stock",
        source="mootdx",
        status=DataFreshStatus.FRESH if has_breadth_data else DataFreshStatus.MISSING,
        fetched_at=breadth_fetched_at or (now if has_breadth_data else None),
        required=True,
    ))

    # Turnover
    statuses.append(DataStatus(
        dataset_name="turnover_data",
        market="cn_stock",
        source="mootdx",
        status=DataFreshStatus.FRESH if has_turnover_data else DataFreshStatus.MISSING,
        fetched_at=turnover_fetched_at or (now if has_turnover_data else None),
        required=True,
    ))

    # Sector data
    statuses.append(DataStatus(
        dataset_name="sector_data",
        market="cn_stock",
        source="eastmoney",
        status=DataFreshStatus.FRESH if has_sector_data else DataFreshStatus.MISSING,
        fetched_at=sector_fetched_at or (now if has_sector_data else None),
        required=True,
    ))

    # Limit up pool
    statuses.append(DataStatus(
        dataset_name="limit_up_pool",
        market="cn_stock",
        source="eastmoney",
        status=DataFreshStatus.FRESH if has_limit_up_pool else DataFreshStatus.MISSING,
        fetched_at=limit_up_fetched_at or (now if has_limit_up_pool else None),
        required=True,
    ))

    # Strong stocks (optional)
    statuses.append(DataStatus(
        dataset_name="strong_stock_rankings",
        market="cn_stock",
        source="mootdx",
        status=DataFreshStatus.FRESH if has_strong_stocks else DataFreshStatus.MISSING,
        fetched_at=now if has_strong_stocks else None,
        required=False,
    ))

    # Attention pool (optional)
    statuses.append(DataStatus(
        dataset_name="attention_pool",
        market="cn_stock",
        source="local_builder",
        status=DataFreshStatus.FRESH if has_attention_pool else DataFreshStatus.MISSING,
        fetched_at=now if has_attention_pool else None,
        required=False,
    ))

    # Announcement (optional)
    statuses.append(DataStatus(
        dataset_name="announcement",
        market="cn_stock",
        source="cninfo",
        status=DataFreshStatus.FRESH if has_announcement else DataFreshStatus.MISSING,
        fetched_at=now if has_announcement else None,
        required=False,
    ))

    return statuses


def check_market_scan_freshness(
    guard: DataFreshnessGuard,
    trade_date: str,
    scan_time: Optional[datetime] = None,
    **kwargs,
) -> bool:
    """Check freshness for Market-Wide Scan.

    Args:
        guard: DataFreshnessGuard instance
        trade_date: Trade date
        scan_time: Scan time
        **kwargs: Arguments for build_market_scan_freshness_status

    Returns:
        True if can continue to theme detection
    """
    statuses = build_market_scan_freshness_status(
        trade_date=trade_date,
        scan_time=scan_time,
        **kwargs,
    )

    result = guard.check_report_freshness(
        market="cn_stock",
        report_type="market_scan",
        dataset_statuses=statuses,
        now=scan_time,
    )

    return result.can_generate_report
