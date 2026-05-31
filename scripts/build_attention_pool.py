#!/usr/bin/env python3
"""
Build Attention Pool from structured hotlist data.

Usage:
    python scripts/build_attention_pool.py
    python scripts/build_attention_pool.py --as-of-date 2026-05-31 --include-legacy --window 20
    python scripts/build_attention_pool.py --include-legacy --use-repaired-legacy

Behavior:
    - Reads structured hotlist data from data/manual_hotlists/structured/
    - Optionally reads legacy import data from data/manual_hotlists/legacy_import/
    - Optionally reads repaired legacy data
    - Builds Attention Pool with configurable scoring
    - Outputs to data/manual_hotlists/attention_pool/
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.markets.cn_stock.hotlist.schema import (
    AttentionScoreConfig,
    HotlistRecord,
)
from tradingagents.markets.cn_stock.hotlist.normalizer import normalize_legacy_record
from tradingagents.markets.cn_stock.hotlist.attention_pool import (
    build_attention_pool,
    generate_build_summary,
    generate_top50_explain,
)
from tradingagents.markets.cn_stock.hotlist.io import (
    load_structured,
    save_attention_pool,
    save_audit_summary,
)


def load_all_structured_data(structured_dir: Path) -> list:
    """Load all structured JSONL files from directory."""
    all_records = []
    for jsonl_file in sorted(structured_dir.glob("*.jsonl")):
        records = load_structured(jsonl_file)
        all_records.extend(records)
    return all_records


def load_legacy_data(legacy_dir: Path) -> list:
    """Load legacy import data."""
    all_records = []
    legacy_file = legacy_dir / "structured" / "tradingagents-old" / "hotlist_legacy_tradingagents_old.jsonl"

    if not legacy_file.exists():
        print(f"Warning: Legacy file not found: {legacy_file}")
        return all_records

    with open(legacy_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    record = normalize_legacy_record(data)
                    all_records.append(record)
                except Exception as e:
                    print(f"Warning: Failed to parse legacy record: {e}")

    return all_records


def load_repaired_legacy_data(legacy_dir: Path) -> list:
    """Load repaired legacy import data."""
    all_records = []
    repaired_file = legacy_dir / "structured" / "tradingagents-old" / "hotlist_legacy_repaired.jsonl"

    if not repaired_file.exists():
        print(f"Warning: Repaired legacy file not found: {repaired_file}")
        return all_records

    with open(repaired_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    # Create HotlistRecord from repaired data
                    record = HotlistRecord(
                        trade_date=data.get("trade_date", ""),
                        source=data.get("source", ""),
                        rank=data.get("rank"),
                        ticker=data.get("ticker", ""),
                        name=data.get("name", ""),
                        board_type=data.get("board_type", "unknown"),
                        is_main_board=data.get("is_main_board"),
                        raw_line=data.get("raw_line", ""),
                        parse_status=data.get("parse_status", "valid"),
                        parse_warnings=data.get("parse_warnings", []),
                        source_project=data.get("source_project", "tradingagents-old"),
                        original_path=data.get("original_path", ""),
                        created_at=data.get("created_at", ""),
                    )
                    all_records.append(record)
                except Exception as e:
                    print(f"Warning: Failed to parse repaired record: {e}")

    return all_records


def deduplicate_records(records: list) -> tuple:
    """Deduplicate records by (trade_date, source, ticker).

    Returns:
        (deduplicated_records, dedup_count)
    """
    seen = set()
    deduped = []
    dedup_count = 0

    for record in records:
        key = (record.trade_date, record.source, record.ticker)
        if key in seen:
            dedup_count += 1
            continue
        seen.add(key)
        deduped.append(record)

    return deduped, dedup_count


def save_csv(entries: list, output_path: Path) -> None:
    """Save Attention Pool as CSV."""
    if not entries:
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            "rank", "ticker", "name", "attention_score_20d", "appear_days_20d",
            "consecutive_days", "latest_trade_date", "latest_rank", "best_rank_20d",
            "avg_rank_20d", "source_count_20d", "sources_20d", "is_main_board",
            "board_type", "data_warnings",
        ])

        # Data
        for i, entry in enumerate(entries, 1):
            writer.writerow([
                i,
                entry.ticker,
                entry.name,
                round(entry.attention_score_20d, 2),
                entry.appear_days_20d,
                entry.consecutive_days,
                entry.latest_trade_date,
                entry.latest_rank,
                entry.best_rank_20d,
                round(entry.avg_rank_20d, 2) if entry.avg_rank_20d is not None else "",
                entry.source_count_20d,
                "; ".join(sorted(entry.sources_20d)),
                "Y" if entry.is_main_board else ("N" if entry.is_main_board is False else "?"),
                entry.board_type,
                "; ".join(entry.data_warnings) if entry.data_warnings else "",
            ])


def main():
    parser = argparse.ArgumentParser(
        description="Build Attention Pool from structured hotlist data"
    )
    parser.add_argument(
        "--as-of-date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="As-of date for the build (default: today)",
    )
    parser.add_argument(
        "--include-legacy",
        action="store_true",
        help="Include legacy import data",
    )
    parser.add_argument(
        "--use-repaired-legacy",
        action="store_true",
        help="Use repaired legacy data instead of original legacy",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=20,
        help="Window size in trade days (default: 20)",
    )

    args = parser.parse_args()

    # Validate date
    try:
        datetime.strptime(args.as_of_date, "%Y-%m-%d")
    except ValueError:
        print(f"Error: Invalid date format: {args.as_of_date}. Expected YYYY-MM-DD.")
        sys.exit(1)

    # Define paths
    data_dir = PROJECT_ROOT / "data" / "manual_hotlists"
    structured_dir = data_dir / "structured"
    legacy_dir = data_dir / "legacy_import"
    output_dir = data_dir / "attention_pool"
    audit_dir = output_dir / "audit"

    # Load data
    print("Loading structured data...")
    all_records = load_all_structured_data(structured_dir)
    print(f"Loaded {len(all_records)} records from structured data")

    # Track repair stats
    repaired_count = 0
    unresolved_count = 0
    conflict_count = 0

    if args.include_legacy:
        if args.use_repaired_legacy:
            # Load BOTH original valid AND repaired records
            print("Loading original legacy data...")
            legacy_records = load_legacy_data(legacy_dir)
            all_records.extend(legacy_records)
            print(f"Loaded {len(legacy_records)} records from original legacy data")

            print("Loading repaired legacy data...")
            repaired_records = load_repaired_legacy_data(legacy_dir)
            all_records.extend(repaired_records)
            print(f"Loaded {len(repaired_records)} records from repaired legacy data")

            # Load repair stats from audit
            repair_summary_path = legacy_dir / "audit" / "tradingagents_old_repair_summary.md"
            if repair_summary_path.exists():
                # Parse repair stats from summary file
                with open(repair_summary_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Simple parsing - look for the values
                    import re
                    repaired_match = re.search(r"repaired_by_stock_name_map.*?\|\s*(\d+)", content)
                    unresolved_match = re.search(r"unresolved.*?\|\s*(\d+)", content)
                    if repaired_match:
                        repaired_count = int(repaired_match.group(1))
                    if unresolved_match:
                        unresolved_count = int(unresolved_match.group(1))
        else:
            print("Loading legacy data...")
            legacy_records = load_legacy_data(legacy_dir)
            all_records.extend(legacy_records)
            print(f"Loaded {len(legacy_records)} records from legacy data")

    if not all_records:
        print("Error: No records found. Nothing to build.")
        sys.exit(1)

    # Deduplicate
    all_records, dedup_count = deduplicate_records(all_records)
    print(f"After deduplication: {len(all_records)} records (removed {dedup_count} duplicates)")

    # Configure scoring
    config = AttentionScoreConfig()
    config.WINDOW_TRADE_DAYS = args.window

    # Build Attention Pool
    print("\nBuilding Attention Pool...")
    pool_entries = build_attention_pool(all_records, config, args.window)
    print(f"Built Attention Pool with {len(pool_entries)} entries")

    # Save output
    save_attention_pool(pool_entries, output_dir, args.as_of_date)
    print(f"\nSaved Attention Pool to: {output_dir}")

    # Save CSV
    csv_path = output_dir / "attention_pool_latest.csv"
    save_csv(pool_entries, csv_path)
    print(f"Saved CSV to: {csv_path}")

    # Generate and save audit summary
    summary = generate_build_summary(
        pool_entries, all_records, config,
        args.include_legacy,
        args.use_repaired_legacy,
        repaired_count, unresolved_count, conflict_count, dedup_count,
    )
    save_audit_summary(summary, audit_dir, "attention_pool_build_summary.md")
    print(f"Saved audit summary to: {audit_dir / 'attention_pool_build_summary.md'}")

    # Generate and save Top 50 explain
    explain_md, explain_json = generate_top50_explain(pool_entries)
    save_audit_summary(explain_md, audit_dir, "attention_pool_top50_explain.md")
    with open(audit_dir / "attention_pool_top50_explain.json", "w", encoding="utf-8") as f:
        json.dump(explain_json, f, ensure_ascii=False, indent=2)
    print(f"Saved Top 50 explain to: {audit_dir / 'attention_pool_top50_explain.md'}")

    # Print top 10
    print("\n=== Top 10 Attention Pool ===")
    print(f"{'Rank':<5} {'Ticker':<12} {'Name':<10} {'Score':<10} {'Days':<6} {'Consec':<8} {'Board'}")
    print("-" * 65)
    for i, entry in enumerate(pool_entries[:10], 1):
        board = "Y" if entry.is_main_board else ("N" if entry.is_main_board is False else "?")
        print(
            f"{i:<5} {entry.ticker:<12} {entry.name:<10} "
            f"{entry.attention_score_20d:<10.1f} {entry.appear_days_20d:<6} "
            f"{entry.consecutive_days:<8} {board}"
        )

    print(f"\nBuild complete: {len(pool_entries)} entries")


if __name__ == "__main__":
    main()
