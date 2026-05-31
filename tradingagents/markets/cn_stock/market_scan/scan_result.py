"""Market-Wide Scan result builder.

This module provides a skeleton function for building Market-Wide Scan results.
It does NOT implement real theme detection or trading recommendations.

NOTE: Phase 3B - skeleton only. No real data fetching, no theme detection algorithm.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from .schema import (
    MarketTemperature,
    MarketWideScanInput,
    MarketWideScanResult,
    RiskLevel,
)


def build_market_wide_scan_result(
    scan_input: MarketWideScanInput,
    now: Optional[datetime] = None,
) -> MarketWideScanResult:
    """Build Market-Wide Scan result from input.

    This is a skeleton function that:
    1. Validates input structure
    2. Generates basic summaries
    3. Checks data freshness
    4. Returns warnings for missing data
    5. Does NOT generate trading recommendations
    6. Does NOT implement theme detection

    Args:
        scan_input: Market-Wide Scan input data
        now: Current time (for testing)

    Returns:
        MarketWideScanResult with basic summaries and warnings
    """
    if now is None:
        now = datetime.now()

    result = MarketWideScanResult(
        trade_date=scan_input.trade_date,
        scan_time=scan_input.scan_time or now,
    )

    # Check basic data availability
    if not scan_input.indexes:
        result.warnings.append("No index data provided")

    if scan_input.market_breadth is None:
        result.warnings.append("No market breadth data provided")
    else:
        total = (
            scan_input.market_breadth.up_count
            + scan_input.market_breadth.down_count
            + scan_input.market_breadth.flat_count
        )
        if total > 0:
            up_pct = scan_input.market_breadth.up_count / total * 100
            result.breadth_summary = (
                f"上涨 {scan_input.market_breadth.up_count} 家, "
                f"下跌 {scan_input.market_breadth.down_count} 家, "
                f"涨停 {scan_input.market_breadth.limit_up_count} 家, "
                f"跌停 {scan_input.market_breadth.limit_down_count} 家, "
                f"炸板 {scan_input.market_breadth.broken_limit_up_count} 家, "
                f"最高连板 {scan_input.market_breadth.high_board_height}"
            )

    if scan_input.turnover is None:
        result.warnings.append("No turnover data provided")
    else:
        result.turnover_summary = (
            f"两市成交额 {scan_input.turnover.total_market_turnover:.0f} 亿元"
        )
        if scan_input.turnover.turnover_change_vs_previous_day is not None:
            change = scan_input.turnover.turnover_change_vs_previous_day
            result.turnover_summary += f"，较前日 {'+' if change >= 0 else ''}{change:.1f}%"

    if not scan_input.sectors:
        result.warnings.append("No sector data provided")
    else:
        # Sort sectors by pct_change
        sorted_sectors = sorted(
            scan_input.sectors, key=lambda s: s.pct_change, reverse=True
        )
        result.strongest_sectors = [s.sector_name for s in sorted_sectors[:5]]
        result.weakest_sectors = [s.sector_name for s in sorted_sectors[-5:]]

    if not scan_input.strong_stocks:
        result.warnings.append("No strong stock data provided")

    if scan_input.limit_up_pool is None:
        result.warnings.append("No limit-up pool data provided")

    # Theme candidates - empty in this phase
    # Will be populated by Theme Detection in a later phase
    result.theme_candidates = []

    # Out-of-pool candidates - empty in this phase
    # Will be populated by Out-of-Pool High Conviction Alert in a later phase
    result.out_of_pool_candidates = []

    # Determine if we can continue to theme detection
    # Key data must be available
    critical_missing = []
    if scan_input.market_breadth is None:
        critical_missing.append("market_breadth")
    if not scan_input.sectors:
        critical_missing.append("sector_data")
    if scan_input.limit_up_pool is None:
        critical_missing.append("limit_up_pool")

    if critical_missing:
        result.can_continue_to_theme_detection = False
        result.blocking_reasons.append(
            f"关键数据缺失: {', '.join(critical_missing)}"
        )

    return result
