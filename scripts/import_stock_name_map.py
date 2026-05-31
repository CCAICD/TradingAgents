#!/usr/bin/env python3
"""
Import stock name mapping from stock-pool.

Usage:
    python scripts/import_stock_name_map.py

Behavior:
    - Reads stock-pool/stock_names.json (read-only)
    - Creates data/reference/stock_name_map.json
    - Creates data/reference/stock_name_map.jsonl
    - Creates data/reference/audit/stock_name_map_import_summary.md
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SOURCE_FILE = Path(r"C:\github\stock-pool\stock_names.json")


def guess_exchange(code: str) -> str:
    """Guess exchange from code prefix."""
    if code.startswith("6"):
        return "SH"
    elif code.startswith(("0", "3")):
        return "SZ"
    elif code.startswith(("4", "8")):
        return "BJ"
    else:
        return "UNKNOWN"


def normalize_ticker(code: str, exchange: str) -> str:
    """Normalize ticker to XXXXXX.SH/SZ/BJ format."""
    return f"{code}.{exchange}"


def is_index_or_etf(name: str, code: str) -> bool:
    """Check if the entry is an index or ETF (not a stock)."""
    index_keywords = ["指数", "等权", "成长", "价值", "资源", "消费", "能源", "信息",
                      "医药", "可选", "工业", "金融", "材料", "电信", "治理", "基建",
                      "运输", "央企", "民企", "国企", "地企", "龙头", "商品", "周期",
                      "沪企", "小盘", "中型", "全指", "全R", "180", "50", "380",
                      "R成长", "R价值", "ETF", "LOF", "基金"]
    for kw in index_keywords:
        if kw in name:
            return True
    # Some codes are indices
    if code.startswith("0000") and int(code) < 100:
        return True
    return False


def main():
    if not SOURCE_FILE.exists():
        print(f"Error: Source file not found: {SOURCE_FILE}")
        sys.exit(1)

    # Read source
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        raw_map = json.load(f)

    print(f"Read {len(raw_map)} entries from {SOURCE_FILE}")

    # Process entries
    entries = []
    index_entries = []
    conflict_entries = []

    seen_tickers = {}

    for code, name in raw_map.items():
        code = code.strip()
        name = name.strip()

        if not code or not name:
            continue

        exchange = guess_exchange(code)
        normalized_ticker = normalize_ticker(code, exchange)

        # Check if index/ETF
        if is_index_or_etf(name, code):
            index_entries.append({
                "ticker": code,
                "normalized_ticker": normalized_ticker,
                "name": name,
                "exchange": exchange,
                "type": "index_etf",
            })
            continue

        # Check for conflicts (same code, different name)
        if code in seen_tickers:
            if seen_tickers[code] != name:
                conflict_entries.append({
                    "ticker": code,
                    "name1": seen_tickers[code],
                    "name2": name,
                })
            continue

        seen_tickers[code] = name

        entries.append({
            "ticker": code,
            "normalized_ticker": normalized_ticker,
            "name": name,
            "exchange": exchange,
            "source_project": "stock-pool",
            "original_path": str(SOURCE_FILE),
            "imported_at": datetime.now().isoformat(),
        })

    # Create output directory
    output_dir = PROJECT_ROOT / "data" / "reference"
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_dir = output_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_path = output_dir / "stock_name_map.json"
    json_map = {e["ticker"]: e["name"] for e in entries}
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_map, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(json_map)} entries to {json_path}")

    # Save JSONL
    jsonl_path = output_dir / "stock_name_map.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Saved {len(entries)} entries to {jsonl_path}")

    # Save audit summary
    summary_path = audit_dir / "stock_name_map_import_summary.md"
    summary = f"""# Stock Name Map Import Summary

> Import time: {datetime.now().isoformat()}
> Source: {SOURCE_FILE}

---

## 一、导入概览

| 项目 | 数值 |
|------|------|
| 原始记录数 | {len(raw_map)} |
| 股票记录数 | {len(entries)} |
| 指数/ETF 记录数 | {len(index_entries)} |
| 冲突记录数 | {len(conflict_entries)} |

## 二、交易所分布

| 交易所 | 记录数 |
|--------|--------|
| SH (上海) | {sum(1 for e in entries if e['exchange'] == 'SH')} |
| SZ (深圳) | {sum(1 for e in entries if e['exchange'] == 'SZ')} |
| BJ (北京) | {sum(1 for e in entries if e['exchange'] == 'BJ')} |
| UNKNOWN | {sum(1 for e in entries if e['exchange'] == 'UNKNOWN')} |

## 三、输出文件

| 文件 | 说明 |
|------|------|
| `stock_name_map.json` | 轻量映射（code → name） |
| `stock_name_map.jsonl` | 完整映射（含元数据） |
| `audit/stock_name_map_import_summary.md` | 本审计报告 |

## 四、用途说明

- 用于修复历史热榜中 name 缺失的记录
- 用于 board_type 离线推断
- **不是实时数据源**
- **不能用于行情判断**

---

**文档结束。**

> 本文档由 import_stock_name_map.py 自动生成于 {datetime.now().isoformat()}。
"""
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"Saved audit summary to {summary_path}")

    # Print summary
    print(f"\nImport complete:")
    print(f"  Stock entries: {len(entries)}")
    print(f"  Index/ETF entries: {len(index_entries)}")
    print(f"  Conflict entries: {len(conflict_entries)}")


if __name__ == "__main__":
    main()
