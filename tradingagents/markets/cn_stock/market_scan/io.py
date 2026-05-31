"""Market-Wide Scan I/O utilities.

This module provides functions for loading and saving Market-Wide Scan data.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .schema import (
    IndexSnapshot,
    LimitUpPoolSnapshot,
    MarketBreadthSnapshot,
    MarketWideScanInput,
    MarketWideScanResult,
    SectorSnapshot,
    StrongStockSnapshot,
    TurnoverSnapshot,
)


def _parse_datetime(s: Optional[str]) -> Optional[datetime]:
    """Parse ISO format datetime string."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def load_market_scan_input(path: Path) -> MarketWideScanInput:
    """Load Market-Wide Scan input from JSON file.

    Args:
        path: Path to JSON file

    Returns:
        MarketWideScanInput
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Parse indexes
    indexes = []
    for d in data.get("indexes", []):
        indexes.append(IndexSnapshot(
            index_code=d.get("index_code", ""),
            index_name=d.get("index_name", ""),
            latest_price=d.get("latest_price", 0),
            pct_change=d.get("pct_change", 0),
            turnover=d.get("turnover"),
            volume=d.get("volume"),
            as_of_time=_parse_datetime(d.get("as_of_time")),
            source=d.get("source", ""),
        ))

    # Parse market breadth
    breadth = None
    if data.get("market_breadth"):
        d = data["market_breadth"]
        breadth = MarketBreadthSnapshot(
            up_count=d.get("up_count", 0),
            down_count=d.get("down_count", 0),
            flat_count=d.get("flat_count", 0),
            limit_up_count=d.get("limit_up_count", 0),
            limit_down_count=d.get("limit_down_count", 0),
            real_limit_up_count=d.get("real_limit_up_count", 0),
            real_limit_down_count=d.get("real_limit_down_count", 0),
            broken_limit_up_count=d.get("broken_limit_up_count", 0),
            limit_up_open_fail_count=d.get("limit_up_open_fail_count", 0),
            high_board_height=d.get("high_board_height", 0),
            as_of_time=_parse_datetime(d.get("as_of_time")),
            source=d.get("source", ""),
        )

    # Parse turnover
    turnover = None
    if data.get("turnover"):
        d = data["turnover"]
        turnover = TurnoverSnapshot(
            total_market_turnover=d.get("total_market_turnover", 0),
            sh_turnover=d.get("sh_turnover"),
            sz_turnover=d.get("sz_turnover"),
            bj_turnover=d.get("bj_turnover"),
            turnover_change_vs_previous_day=d.get("turnover_change_vs_previous_day"),
            as_of_time=_parse_datetime(d.get("as_of_time")),
            source=d.get("source", ""),
        )

    # Parse sectors
    sectors = []
    for d in data.get("sectors", []):
        sectors.append(SectorSnapshot(
            sector_code=d.get("sector_code", ""),
            sector_name=d.get("sector_name", ""),
            pct_change=d.get("pct_change", 0),
            turnover=d.get("turnover"),
            turnover_rank=d.get("turnover_rank"),
            limit_up_count=d.get("limit_up_count", 0),
            strong_stock_count=d.get("strong_stock_count", 0),
            leading_stocks=d.get("leading_stocks", []),
            source=d.get("source", ""),
            as_of_time=_parse_datetime(d.get("as_of_time")),
        ))

    # Parse strong stocks
    strong_stocks = []
    for d in data.get("strong_stocks", []):
        strong_stocks.append(StrongStockSnapshot(
            ticker=d.get("ticker", ""),
            name=d.get("name", ""),
            pct_change=d.get("pct_change", 0),
            turnover=d.get("turnover"),
            rank_by_turnover=d.get("rank_by_turnover"),
            rank_by_pct_change=d.get("rank_by_pct_change"),
            is_limit_up=d.get("is_limit_up", False),
            is_broken_limit_up=d.get("is_broken_limit_up", False),
            board_type=d.get("board_type", ""),
            sector_names=d.get("sector_names", []),
            source=d.get("source", ""),
            as_of_time=_parse_datetime(d.get("as_of_time")),
        ))

    # Parse limit up pool
    limit_up_pool = None
    if data.get("limit_up_pool"):
        d = data["limit_up_pool"]
        limit_up_pool = LimitUpPoolSnapshot(
            trade_date=d.get("trade_date", ""),
            limit_up_stocks=d.get("limit_up_stocks", []),
            limit_down_stocks=d.get("limit_down_stocks", []),
            broken_limit_up_stocks=d.get("broken_limit_up_stocks", []),
            high_board_height=d.get("high_board_height", 0),
            source=d.get("source", ""),
            as_of_time=_parse_datetime(d.get("as_of_time")),
        )

    return MarketWideScanInput(
        trade_date=data.get("trade_date", ""),
        scan_time=_parse_datetime(data.get("scan_time")),
        indexes=indexes,
        market_breadth=breadth,
        turnover=turnover,
        sectors=sectors,
        strong_stocks=strong_stocks,
        limit_up_pool=limit_up_pool,
    )


def save_market_scan_result(
    result: MarketWideScanResult,
    output_path: Path,
) -> None:
    """Save Market-Wide Scan result to JSON file.

    Args:
        result: Market-Wide Scan result
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
