"""Parser for manual hotlist text input.

Parses natural language or copied text from platforms like 同花顺, 东方财富, 雪球, 通达信.
This is a v0.1 implementation - not perfect, but handles common formats.
"""

from __future__ import annotations

import re
from typing import List, Tuple, Optional
from datetime import datetime

from .schema import HotlistRecord, VALID_SOURCES


# Patterns for platform detection
PLATFORM_PATTERNS = [
    (re.compile(r"同花顺|tonghuashun|ths", re.IGNORECASE), "同花顺"),
    (re.compile(r"东方财富|eastmoney|dfcf", re.IGNORECASE), "东方财富"),
    (re.compile(r"雪球|xueqiu", re.IGNORECASE), "雪球"),
    (re.compile(r"通达信|tongdaxin|tdx", re.IGNORECASE), "通达信"),
]

# Pattern for rank detection
RANK_PATTERN = re.compile(
    r"^(?:第?\s*)?(\d{1,2})\s*[.、)）\]\]】]\s*"
)

# Pattern for stock code (6 digits with optional suffix)
TICKER_PATTERN = re.compile(
    r"(\d{6})(?:\.(SH|SZ|sh|sz))?"
)

# Pattern for date detection
DATE_PATTERN = re.compile(
    r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)"
)


def _detect_platform(line: str) -> Optional[str]:
    """Detect platform from a line of text."""
    for pattern, platform in PLATFORM_PATTERNS:
        if pattern.search(line):
            return platform
    return None


def _extract_rank(line: str) -> Tuple[Optional[int], str]:
    """Extract rank from line. Returns (rank, remaining_line)."""
    match = RANK_PATTERN.match(line.strip())
    if match:
        rank = int(match.group(1))
        if 1 <= rank <= 100:  # Reasonable rank range
            remaining = line[match.end():]
            return rank, remaining
    return None, line


def _extract_ticker(text: str) -> Tuple[str, str]:
    """Extract ticker from text. Returns (ticker, remaining_text)."""
    match = TICKER_PATTERN.search(text)
    if match:
        code = match.group(1)
        suffix = match.group(2)
        if suffix:
            suffix = suffix.upper()
        else:
            # Guess suffix based on code
            if code.startswith("6"):
                suffix = "SH"
            elif code.startswith(("0", "3")):
                suffix = "SZ"
            elif code.startswith(("4", "8")):
                suffix = "BJ"  # Beijing Stock Exchange
            else:
                suffix = "SH"  # Default
        ticker = f"{code}.{suffix}"
        remaining = text[:match.start()] + text[match.end():]
        return ticker, remaining
    return "", text


def _extract_name(text: str) -> str:
    """Extract stock name from text (what remains after ticker extraction)."""
    # Clean up the text
    name = text.strip()
    # Remove common separators
    name = re.sub(r"[\s\-—–,，、;；]+", "", name)
    # Remove empty brackets
    name = re.sub(r"[()（）\[\]【】{}]+", "", name)
    return name.strip()


def _is_main_board(ticker: str) -> Optional[bool]:
    """Check if ticker is main board."""
    from .normalizer import infer_board_type
    _, is_main = infer_board_type(ticker)
    return is_main


def _get_board_type(ticker: str) -> str:
    """Get board type from ticker."""
    from .normalizer import infer_board_type
    board_type, _ = infer_board_type(ticker)
    return board_type


def _parse_date_from_text(text: str) -> Optional[str]:
    """Try to extract date from text."""
    match = DATE_PATTERN.search(text)
    if match:
        date_str = match.group(1)
        # Normalize date format
        date_str = date_str.replace("年", "-").replace("月", "-").replace("日", "")
        date_str = date_str.replace("/", "-")
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def parse_hotlist_text(
    text: str,
    trade_date: Optional[str] = None,
    source_project: str = "manual_input",
    original_path: str = "",
) -> Tuple[List[HotlistRecord], List[HotlistRecord]]:
    """Parse hotlist text into valid and invalid records.

    Args:
        text: Raw text input containing hotlist data
        trade_date: Trade date (YYYY-MM-DD). If None, try to extract from text.
        source_project: Source project identifier
        original_path: Original file path

    Returns:
        (valid_records, invalid_records)
    """
    valid_records: List[HotlistRecord] = []
    invalid_records: List[HotlistRecord] = []

    # Try to extract date from text if not provided
    if trade_date is None:
        trade_date = _parse_date_from_text(text)

    # Validate date format
    if trade_date is None or not re.match(r"^\d{4}-\d{2}-\d{2}$", trade_date):
        # Cannot determine date - all records invalid
        invalid_records.append(HotlistRecord(
            trade_date=trade_date or "unknown",
            source="unknown",
            raw_line=text[:200],
            parse_status="invalid",
            parse_warnings=["Cannot determine trade date from text"],
            source_project=source_project,
            original_path=original_path,
        ))
        return valid_records, invalid_records

    current_platform: Optional[str] = None
    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if this line is a platform header
        detected_platform = _detect_platform(line)
        if detected_platform:
            current_platform = detected_platform
            # Check if this line also contains data after the platform name
            # Remove the platform part and check for data
            remaining = line
            for pattern, _ in PLATFORM_PATTERNS:
                remaining = pattern.sub("", remaining).strip()
            if not remaining or len(remaining) < 3:
                continue  # Pure header line
            # Otherwise, fall through to parse the remaining part
            line = remaining

        if current_platform is None:
            # No platform detected yet - skip or try to infer
            # Check if it looks like a data line
            if TICKER_PATTERN.search(line):
                # Has a ticker but no platform - mark as warning
                rank, remaining = _extract_rank(line)
                ticker, remaining = _extract_ticker(remaining)
                name = _extract_name(remaining)

                if ticker and name:
                    record = HotlistRecord(
                        trade_date=trade_date,
                        source="unknown",
                        rank=rank,
                        ticker=ticker,
                        name=name,
                        board_type=_get_board_type(ticker),
                        is_main_board=_is_main_board(ticker),
                        raw_line=line,
                        parse_status="warning",
                        parse_warnings=["Platform not detected"],
                        source_project=source_project,
                        original_path=original_path,
                    )
                    invalid_records.append(record)
            continue

        # Parse data line
        rank, remaining = _extract_rank(line)
        ticker, remaining = _extract_ticker(remaining)
        name = _extract_name(remaining)

        # Validate
        warnings = []
        if not ticker:
            warnings.append("Missing ticker")
        if not name:
            warnings.append("Missing name")
        if rank is None:
            warnings.append("Missing rank")

        if ticker and name:
            record = HotlistRecord(
                trade_date=trade_date,
                source=current_platform,
                rank=rank,
                ticker=ticker,
                name=name,
                board_type=_get_board_type(ticker),
                is_main_board=_is_main_board(ticker),
                raw_line=line,
                parse_status="warning" if warnings else "valid",
                parse_warnings=warnings,
                source_project=source_project,
                original_path=original_path,
            )
            valid_records.append(record)
        else:
            record = HotlistRecord(
                trade_date=trade_date,
                source=current_platform,
                rank=rank,
                ticker=ticker,
                name=name,
                board_type=_get_board_type(ticker) if ticker else "unknown",
                is_main_board=_is_main_board(ticker) if ticker else None,
                raw_line=line,
                parse_status="invalid",
                parse_warnings=warnings,
                source_project=source_project,
                original_path=original_path,
            )
            invalid_records.append(record)

    return valid_records, invalid_records
