#!/usr/bin/env python3
"""
Import manual hotlist text into structured format.

Usage:
    python scripts/import_manual_hotlist.py --date 2026-05-31 --input path/to/raw.txt
    python scripts/import_manual_hotlist.py --date 2026-05-31 --input path/to/raw.txt --rebuild

Behavior:
    - Reads raw text file
    - Saves raw text to data/manual_hotlists/raw_text/YYYY-MM-DD.md
    - Parses and saves structured records to data/manual_hotlists/structured/YYYY-MM-DD.jsonl
    - Appends events to data/manual_hotlists/events/hotlist_events.jsonl
    - Saves invalid records to data/manual_hotlists/attention_pool/audit/YYYY-MM-DD_invalid_records.jsonl
    - With --rebuild, overwrites structured file for that date
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.markets.cn_stock.hotlist.parser import parse_hotlist_text
from tradingagents.markets.cn_stock.hotlist.normalizer import normalize_record
from tradingagents.markets.cn_stock.hotlist.io import (
    save_structured,
    save_raw_text,
    save_invalid_records,
)


def main():
    parser = argparse.ArgumentParser(
        description="Import manual hotlist text into structured format"
    )
    parser.add_argument(
        "--date",
        required=True,
        help="Trade date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to raw text file",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild structured file for this date (overwrite)",
    )
    parser.add_argument(
        "--source-project",
        default="manual_input",
        help="Source project identifier (default: manual_input)",
    )

    args = parser.parse_args()

    # Validate date
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print(f"Error: Invalid date format: {args.date}. Expected YYYY-MM-DD.")
        sys.exit(1)

    # Read input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    raw_text = input_path.read_text(encoding="utf-8")
    if not raw_text.strip():
        print("Error: Input file is empty.")
        sys.exit(1)

    # Define paths
    data_dir = PROJECT_ROOT / "data" / "manual_hotlists"
    raw_text_dir = data_dir / "raw_text"
    structured_dir = data_dir / "structured"
    events_dir = data_dir / "events"
    audit_dir = data_dir / "attention_pool" / "audit"

    # Check if structured file already exists
    structured_path = structured_dir / f"{args.date}.jsonl"
    if structured_path.exists() and not args.rebuild:
        print(f"Warning: Structured file already exists: {structured_path}")
        print("Use --rebuild to overwrite.")
        sys.exit(1)

    # Save raw text
    raw_text_path = raw_text_dir / f"{args.date}.md"
    save_raw_text(raw_text, raw_text_path)
    print(f"Saved raw text: {raw_text_path}")

    # Parse text
    valid_records, invalid_records = parse_hotlist_text(
        raw_text,
        trade_date=args.date,
        source_project=args.source_project,
        original_path=str(input_path),
    )

    # Normalize records
    valid_records = [normalize_record(r) for r in valid_records]
    invalid_records = [normalize_record(r) for r in invalid_records]

    # Save structured records
    count = save_structured(valid_records, structured_path)
    print(f"Saved {count} valid records: {structured_path}")

    # Save invalid records
    if invalid_records:
        invalid_count = save_invalid_records(invalid_records, audit_dir, args.date)
        print(f"Saved {invalid_count} invalid records to audit")

    # Append to events log
    events_path = events_dir / "hotlist_events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "event_type": "hotlist_import",
        "trade_date": args.date,
        "timestamp": datetime.now().isoformat(),
        "source_project": args.source_project,
        "input_path": str(input_path),
        "valid_count": len(valid_records),
        "invalid_count": len(invalid_records),
        "rebuild": args.rebuild,
    }

    with open(events_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(f"Appended event to: {events_path}")
    print(f"\nImport complete: {len(valid_records)} valid, {len(invalid_records)} invalid")


if __name__ == "__main__":
    main()
