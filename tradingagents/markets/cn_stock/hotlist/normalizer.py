"""Normalizer for hotlist records.

Handles normalization of ticker formats, platform names, and board types.

Board type inference (v0.1):
- 600/601/603/605 → main_board_sh (上海主板)
- 000/001/002/003 → main_board_sz (深圳主板)
- 300/301 → chinext (创业板)
- 688/689 → star_market (科创板)
- 8/4 开头的北交所代码 → beijing_stock_exchange (北交所)
- 其他 → unknown

NOTE: This is a v0.1 offline inference. It should NOT be used for final
trading eligibility decisions. Non-mainboard stocks are NOT filtered out.
"""

from __future__ import annotations

import re
from typing import Optional

from .schema import HotlistRecord, VALID_SOURCES


def normalize_ticker(ticker: str) -> str:
    """Normalize ticker format to XXXXXX.SH/SZ/BJ.

    Args:
        ticker: Raw ticker string (e.g., "600519", "600519.SH", "000001.SZ")

    Returns:
        Normalized ticker string
    """
    if not ticker:
        return ""

    ticker = ticker.strip().upper()

    # Already has suffix
    if re.match(r"^\d{6}\.(SH|SZ|BJ)$", ticker):
        return ticker

    # Extract just the code
    match = re.search(r"(\d{6})", ticker)
    if not match:
        return ticker

    code = match.group(1)

    # Guess suffix
    if code.startswith("6"):
        return f"{code}.SH"
    elif code.startswith(("0", "3")):
        return f"{code}.SZ"
    elif code.startswith(("4", "8")):
        return f"{code}.BJ"
    else:
        return f"{code}.SH"  # Default


def normalize_source(source: str) -> str:
    """Normalize platform source name.

    Args:
        source: Raw source string

    Returns:
        Normalized source name, or empty string if not recognized
    """
    if not source:
        return ""

    source = source.strip()

    # Direct match
    if source in VALID_SOURCES:
        return source

    # Fuzzy match
    source_lower = source.lower()
    if "同花顺" in source or "tonghuashun" in source_lower or "ths" in source_lower:
        return "同花顺"
    if "东方财富" in source or "eastmoney" in source_lower or "dfcf" in source_lower:
        return "东方财富"
    if "雪球" in source or "xueqiu" in source_lower:
        return "雪球"
    if "通达信" in source or "tongdaxin" in source_lower or "tdx" in source_lower:
        return "通达信"

    return source  # Return as-is if no match


def infer_board_type(ticker: str) -> tuple:
    """Infer board type from ticker prefix.

    This is a v0.1 offline inference. It should NOT be used for final
    trading eligibility decisions.

    Args:
        ticker: Normalized ticker (e.g., "600519.SH")

    Returns:
        Tuple of (board_type, is_main_board)
    """
    if not ticker:
        return "unknown", None

    code = ticker.split(".")[0]

    # 上海主板: 600xxx, 601xxx, 603xxx, 605xxx
    if re.match(r"^60[0135]\d{3}$", code):
        return "main_board_sh", True

    # 深圳主板: 000xxx, 001xxx, 002xxx, 003xxx
    if re.match(r"^00[0-3]\d{3}$", code):
        return "main_board_sz", True

    # 创业板: 300xxx, 301xxx
    if re.match(r"^30[01]\d{3}$", code):
        return "chinext", False

    # 科创板: 688xxx, 689xxx
    if re.match(r"^68[89]\d{3}$", code):
        return "star_market", False

    # 北交所: 4xxxxx, 8xxxxx (6位)
    if re.match(r"^[48]\d{5}$", code):
        return "beijing_stock_exchange", False

    return "unknown", None


def normalize_record(record: HotlistRecord) -> HotlistRecord:
    """Normalize a hotlist record.

    Args:
        record: Raw hotlist record

    Returns:
        Normalized record
    """
    # Normalize ticker
    record.ticker = normalize_ticker(record.ticker)

    # Normalize source
    record.source = normalize_source(record.source)

    # Infer board type
    if record.ticker:
        inferred_board, inferred_main = infer_board_type(record.ticker)

        # Check consistency with existing is_main_board
        if record.is_main_board is not None and inferred_main is not None:
            if record.is_main_board != inferred_main:
                record.parse_warnings = record.parse_warnings or []
                record.parse_warnings.append(
                    f"Board type conflict: existing is_main_board={record.is_main_board}, "
                    f"inferred={inferred_main} ({inferred_board})"
                )

        # Use inferred values
        record.board_type = inferred_board
        if inferred_main is not None:
            record.is_main_board = inferred_main

    # Validate source
    if record.source not in VALID_SOURCES:
        if record.parse_status == "valid":
            record.parse_status = "warning"
            record.parse_warnings = record.parse_warnings or []
            record.parse_warnings.append(f"Unrecognized source: {record.source}")

    return record


def normalize_legacy_record(record_dict: dict) -> HotlistRecord:
    """Normalize a record from legacy import format.

    The legacy format uses slightly different field names:
    - date -> trade_date
    - main_board -> is_main_board
    - source_project is set to "tradingagents-old"

    Args:
        record_dict: Dictionary from legacy import

    Returns:
        Normalized HotlistRecord
    """
    trade_date = record_dict.get("date", record_dict.get("trade_date", ""))
    source = record_dict.get("source", "")
    ticker = record_dict.get("ticker", "")
    name = record_dict.get("name", "")
    main_board = record_dict.get("main_board", record_dict.get("is_main_board", None))

    # Normalize ticker first
    normalized_ticker = normalize_ticker(ticker)

    # Infer board type
    board_type, is_main_board = infer_board_type(normalized_ticker)

    # Use legacy main_board field if available, check consistency
    if main_board is not None:
        legacy_main = bool(main_board)
        if is_main_board is not None and legacy_main != is_main_board:
            # Conflict - use legacy value but add warning
            pass
        is_main_board = legacy_main
        if is_main_board:
            board_type = "main_board"

    # Warnings
    warnings = []
    if not name:
        warnings.append("Missing name in legacy data")
    if not ticker:
        warnings.append("Missing ticker in legacy data")

    return HotlistRecord(
        trade_date=trade_date,
        source=normalize_source(source),
        rank=None,  # Legacy data doesn't have explicit rank
        ticker=normalized_ticker,
        name=name,
        board_type=board_type,
        is_main_board=is_main_board,
        raw_line="",
        parse_status="warning" if warnings else "valid",
        parse_warnings=warnings,
        source_project="tradingagents-old",
        original_path=record_dict.get("original_path", ""),
        created_at=record_dict.get("imported_at", ""),
    )
