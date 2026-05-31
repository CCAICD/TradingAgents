"""I/O utilities for hotlist data.

Handles reading and writing of structured hotlist data, attention pool,
and related files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .schema import AttentionPoolEntry, HotlistRecord


def save_structured(
    records: List[HotlistRecord],
    output_path: Path,
) -> int:
    """Save structured hotlist records to JSONL file.

    Args:
        records: List of hotlist records
        output_path: Output file path

    Returns:
        Number of records written
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    return len(records)


def load_structured(input_path: Path) -> List[HotlistRecord]:
    """Load structured hotlist records from JSONL file.

    Args:
        input_path: Input file path

    Returns:
        List of hotlist records
    """
    if not input_path.exists():
        return []

    records = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    records.append(HotlistRecord.from_dict(data))
                except json.JSONDecodeError:
                    continue

    return records


def save_raw_text(
    text: str,
    output_path: Path,
) -> None:
    """Save raw hotlist text to file.

    Args:
        text: Raw text content
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def load_raw_text(input_path: Path) -> str:
    """Load raw hotlist text from file.

    Args:
        input_path: Input file path

    Returns:
        Text content
    """
    if not input_path.exists():
        return ""
    return input_path.read_text(encoding="utf-8")


def save_attention_pool(
    entries: List[AttentionPoolEntry],
    output_dir: Path,
    as_of_date: str,
) -> None:
    """Save Attention Pool to files.

    Args:
        entries: List of attention pool entries
        output_dir: Output directory
        as_of_date: Date string for filenames
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save as JSON (array)
    json_path = output_dir / "attention_pool_latest.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in entries], f, ensure_ascii=False, indent=2)

    # Save as JSONL
    jsonl_path = output_dir / "attention_pool_latest.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    # Save by date
    by_date_dir = output_dir / "by_date"
    by_date_dir.mkdir(parents=True, exist_ok=True)
    by_date_path = by_date_dir / f"{as_of_date}.json"
    with open(by_date_path, "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in entries], f, ensure_ascii=False, indent=2)


def load_attention_pool(input_path: Path) -> List[AttentionPoolEntry]:
    """Load Attention Pool from JSON file.

    Args:
        input_path: Input JSON file path

    Returns:
        List of attention pool entries
    """
    if not input_path.exists():
        return []

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = []
    for d in data:
        entry = AttentionPoolEntry(
            ticker=d.get("ticker", ""),
            name=d.get("name", ""),
            attention_score_20d=d.get("attention_score_20d", 0),
            appear_days_20d=d.get("appear_days_20d", 0),
            consecutive_days=d.get("consecutive_days", 0),
            latest_trade_date=d.get("latest_trade_date", ""),
            latest_rank=d.get("latest_rank"),
            best_rank_20d=d.get("best_rank_20d"),
            avg_rank_20d=d.get("avg_rank_20d"),
            source_count_20d=d.get("source_count_20d", 0),
            sources_20d=d.get("sources_20d", []),
            latest_sources=d.get("latest_sources", []),
            first_seen_date_20d=d.get("first_seen_date_20d", ""),
            is_main_board=d.get("is_main_board"),
            board_type=d.get("board_type", "unknown"),
            source_projects=d.get("source_projects", []),
            data_warnings=d.get("data_warnings", []),
            raw_record_count=d.get("raw_record_count", 0),
        )
        entries.append(entry)

    return entries


def save_audit_summary(
    summary: str,
    output_dir: Path,
    filename: str = "attention_pool_build_summary.md",
) -> None:
    """Save audit summary to file.

    Args:
        summary: Markdown summary content
        output_dir: Output directory
        filename: Output filename
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    output_path.write_text(summary, encoding="utf-8")


def save_invalid_records(
    records: List[HotlistRecord],
    output_dir: Path,
    date_str: str,
) -> int:
    """Save invalid records to audit file.

    Args:
        records: List of invalid records
        output_dir: Output directory
        date_str: Date string for filename

    Returns:
        Number of records written
    """
    if not records:
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{date_str}_invalid_records.jsonl"

    with open(output_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    return len(records)
