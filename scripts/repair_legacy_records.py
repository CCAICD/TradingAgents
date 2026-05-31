#!/usr/bin/env python3
"""
Repair legacy invalid records using stock name mapping.

Usage:
    python scripts/repair_legacy_records.py

Behavior:
    - Reads legacy invalid records from data/manual_hotlists/legacy_import/audit/
    - Uses stock name mapping to fill missing names
    - Outputs repaired records to data/manual_hotlists/legacy_import/structured/tradingagents-old/
    - Generates audit reports
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_name_map(json_path: Path) -> dict:
    """Load stock name mapping from JSON file."""
    if not json_path.exists():
        print(f"Warning: Name map file not found: {json_path}")
        return {}
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_code_from_ticker(ticker: str) -> str:
    """Extract 6-digit code from ticker."""
    if not ticker:
        return ""
    parts = ticker.split(".")
    return parts[0] if parts else ""


def main():
    # Define paths
    invalid_path = PROJECT_ROOT / "data" / "manual_hotlists" / "legacy_import" / "audit" / "tradingagents_old_invalid_records.jsonl"
    name_map_path = PROJECT_ROOT / "data" / "reference" / "stock_name_map.json"
    output_dir = PROJECT_ROOT / "data" / "manual_hotlists" / "legacy_import" / "structured" / "tradingagents-old"
    audit_dir = PROJECT_ROOT / "data" / "manual_hotlists" / "legacy_import" / "audit"

    # Load name mapping
    name_map = load_name_map(name_map_path)
    if not name_map:
        print("Error: No name mapping available. Run import_stock_name_map.py first.")
        sys.exit(1)

    print(f"Loaded {len(name_map)} name mappings")

    # Read invalid records
    if not invalid_path.exists():
        print(f"Warning: Invalid records file not found: {invalid_path}")
        print("No records to repair.")
        sys.exit(0)

    invalid_records = []
    with open(invalid_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    invalid_records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    print(f"Read {len(invalid_records)} invalid records")

    # Repair records
    repaired_records = []
    unresolved_records = []
    conflict_records = []

    for record in invalid_records:
        raw_record = record.get("_raw_record", {})
        ticker = raw_record.get("ticker", "")
        original_name = raw_record.get("name", "")

        # Extract code from ticker
        code = extract_code_from_ticker(ticker)

        if not code:
            # No ticker - cannot repair
            record["repair_status"] = "no_ticker"
            unresolved_records.append(record)
            continue

        if original_name:
            # Already has name - no repair needed
            record["repair_status"] = "already_has_name"
            repaired_records.append(record)
            continue

        # Try to find name in mapping
        mapped_name = name_map.get(code)

        if mapped_name:
            # Repair successful
            raw_record["name"] = mapped_name
            record["_raw_record"] = raw_record
            record["repair_status"] = "repaired_by_stock_name_map"
            record["_repair_source"] = "stock-pool"
            record["_repair_timestamp"] = datetime.now().isoformat()

            # Update the record fields
            record["trade_date"] = raw_record.get("date", record.get("trade_date", ""))
            record["source"] = raw_record.get("source", record.get("source", ""))
            record["ticker"] = raw_record.get("ticker", record.get("ticker", ""))
            record["name"] = mapped_name
            record["parse_status"] = "valid"
            record["parse_warnings"] = [w for w in record.get("parse_warnings", []) if "Missing name" not in w]

            repaired_records.append(record)
        else:
            # Cannot find name
            record["repair_status"] = "unresolved"
            unresolved_records.append(record)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)

    # Save repaired records
    repaired_path = output_dir / "hotlist_legacy_repaired.jsonl"
    with open(repaired_path, "w", encoding="utf-8") as f:
        for record in repaired_records:
            # Create a clean record for output
            output_record = {
                "trade_date": record.get("trade_date", ""),
                "source": record.get("source", ""),
                "rank": record.get("rank"),
                "ticker": record.get("ticker", ""),
                "name": record.get("name", ""),
                "board_type": record.get("board_type", "unknown"),
                "is_main_board": record.get("is_main_board"),
                "raw_line": record.get("raw_line", ""),
                "parse_status": record.get("parse_status", "valid"),
                "parse_warnings": record.get("parse_warnings", []),
                "source_project": "tradingagents-old",
                "original_path": record.get("_original_path", ""),
                "created_at": record.get("_repair_timestamp", ""),
                "repair_status": record.get("repair_status", ""),
            }
            f.write(json.dumps(output_record, ensure_ascii=False) + "\n")

    print(f"Saved {len(repaired_records)} repaired records to {repaired_path}")

    # Save unresolved records
    unresolved_path = audit_dir / "tradingagents_old_unresolved_records.jsonl"
    with open(unresolved_path, "w", encoding="utf-8") as f:
        for record in unresolved_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Saved {len(unresolved_records)} unresolved records to {unresolved_path}")

    # Save conflict records (empty in this case)
    conflict_path = audit_dir / "tradingagents_old_repair_conflicts.jsonl"
    with open(conflict_path, "w", encoding="utf-8") as f:
        for record in conflict_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Saved {len(conflict_records)} conflict records to {conflict_path}")

    # Generate audit summary
    summary_path = audit_dir / "tradingagents_old_repair_summary.md"
    summary = f"""# Legacy Records Repair Summary

> Repair time: {datetime.now().isoformat()}
> Source: {invalid_path}

---

## 一、修复概览

| 项目 | 数值 |
|------|------|
| 原始无效记录数 | {len(invalid_records)} |
| 修复成功记录数 | {len([r for r in repaired_records if r.get("repair_status") == "repaired_by_stock_name_map"])} |
| 已有名称记录数 | {len([r for r in repaired_records if r.get("repair_status") == "already_has_name"])} |
| 无法修复记录数 | {len(unresolved_records)} |
| 冲突记录数 | {len(conflict_records)} |

## 二、修复状态分布

| 状态 | 数量 |
|------|------|
| repaired_by_stock_name_map | {len([r for r in repaired_records if r.get("repair_status") == "repaired_by_stock_name_map"])} |
| already_has_name | {len([r for r in repaired_records if r.get("repair_status") == "already_has_name"])} |
| no_ticker | {len([r for r in unresolved_records if r.get("repair_status") == "no_ticker"])} |
| unresolved | {len([r for r in unresolved_records if r.get("repair_status") == "unresolved"])} |

## 三、输出文件

| 文件 | 说明 |
|------|------|
| `hotlist_legacy_repaired.jsonl` | 修复后的记录 |
| `tradingagents_old_unresolved_records.jsonl` | 无法修复的记录 |
| `tradingagents_old_repair_conflicts.jsonl` | 冲突记录 |
| `tradingagents_old_repair_summary.md` | 本审计报告 |

## 四、用途说明

- 修复后的记录可用于 Attention Pool 构建
- 修复状态为 `repaired_by_stock_name_map` 的记录已通过 stock_name_map 补全名称
- 无法修复的记录（unresolved）不进入 Attention Pool
- 所有修复均保留来源和审计记录

---

**文档结束。**

> 本文档由 repair_legacy_records.py 自动生成于 {datetime.now().isoformat()}。
"""
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"Saved audit summary to {summary_path}")

    # Print summary
    repaired_count = len([r for r in repaired_records if r.get("repair_status") == "repaired_by_stock_name_map"])
    print(f"\nRepair complete:")
    print(f"  Repaired: {repaired_count}")
    print(f"  Unresolved: {len(unresolved_records)}")
    print(f"  Conflicts: {len(conflict_records)}")


if __name__ == "__main__":
    main()
