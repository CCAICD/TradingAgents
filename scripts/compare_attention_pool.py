#!/usr/bin/env python3
"""
Generate comparison report between original and repaired legacy builds.

Usage:
    python scripts/compare_attention_pool.py

Behavior:
    - Builds Attention Pool with original legacy
    - Builds Attention Pool with repaired legacy
    - Generates comparison report
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.markets.cn_stock.hotlist.schema import AttentionScoreConfig
from tradingagents.markets.cn_stock.hotlist.normalizer import normalize_legacy_record
from tradingagents.markets.cn_stock.hotlist.attention_pool import build_attention_pool
from tradingagents.markets.cn_stock.hotlist.io import load_structured


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
        return all_records

    with open(legacy_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    record = normalize_legacy_record(data)
                    all_records.append(record)
                except Exception:
                    continue

    return all_records


def load_repaired_legacy_data(legacy_dir: Path) -> list:
    """Load repaired legacy import data."""
    all_records = []
    repaired_file = legacy_dir / "structured" / "tradingagents-old" / "hotlist_legacy_repaired.jsonl"

    if not repaired_file.exists():
        return all_records

    with open(repaired_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    record = __import__('tradingagents.markets.cn_stock.hotlist.schema', fromlist=['HotlistRecord']).HotlistRecord(
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
                except Exception:
                    continue

    return all_records


def main():
    # Define paths
    data_dir = PROJECT_ROOT / "data" / "manual_hotlists"
    structured_dir = data_dir / "structured"
    legacy_dir = data_dir / "legacy_import"
    audit_dir = data_dir / "attention_pool" / "audit"

    config = AttentionScoreConfig()
    window = 20
    config.WINDOW_TRADE_DAYS = window

    # Load official structured data
    print("Loading official structured data...")
    official_records = load_all_structured_data(structured_dir)
    print(f"Loaded {len(official_records)} official records")

    # Load original legacy data
    print("Loading original legacy data...")
    original_legacy = load_legacy_data(legacy_dir)
    print(f"Loaded {len(original_legacy)} original legacy records")

    # Load repaired legacy data
    print("Loading repaired legacy data...")
    repaired_legacy = load_repaired_legacy_data(legacy_dir)
    print(f"Loaded {len(repaired_legacy)} repaired legacy records")

    # Build without repaired
    print("\nBuilding without repaired legacy...")
    records_without = official_records + original_legacy
    pool_without = build_attention_pool(records_without, config, window)
    print(f"Result: {len(pool_without)} stocks")

    # Build with repaired
    print("\nBuilding with repaired legacy...")
    records_with = official_records + original_legacy + repaired_legacy
    pool_with = build_attention_pool(records_with, config, window)
    print(f"Result: {len(pool_with)} stocks")

    # Generate comparison
    tickers_without = {e.ticker: e for e in pool_without}
    tickers_with = {e.ticker: e for e in pool_with}

    new_tickers = set(tickers_with.keys()) - set(tickers_without.keys())
    removed_tickers = set(tickers_without.keys()) - set(tickers_with.keys())
    common_tickers = set(tickers_without.keys()) & set(tickers_with.keys())

    # Rank changes
    rank_without = {e.ticker: i+1 for i, e in enumerate(pool_without)}
    rank_with = {e.ticker: i+1 for i, e in enumerate(pool_with)}

    rank_changes = []
    for ticker in common_tickers:
        old_rank = rank_without.get(ticker, 999)
        new_rank = rank_with.get(ticker, 999)
        rank_changes.append({
            "ticker": ticker,
            "name": tickers_with[ticker].name,
            "old_rank": old_rank,
            "new_rank": new_rank,
            "change": old_rank - new_rank,
            "old_score": tickers_without[ticker].attention_score_20d,
            "new_score": tickers_with[ticker].attention_score_20d,
        })

    rank_changes.sort(key=lambda x: x["change"], reverse=True)

    # Score changes
    score_changes = []
    for ticker in common_tickers:
        old_score = tickers_without[ticker].attention_score_20d
        new_score = tickers_with[ticker].attention_score_20d
        score_changes.append({
            "ticker": ticker,
            "name": tickers_with[ticker].name,
            "old_score": old_score,
            "new_score": new_score,
            "change": new_score - old_score,
        })

    score_changes.sort(key=lambda x: x["change"], reverse=True)

    # Generate report
    report_lines = [
        "# Attention Pool: Original vs Repaired Legacy Comparison",
        "",
        f"> Generated: {datetime.now().isoformat()}",
        "",
        "---",
        "",
        "## 一、构建概览",
        "",
        "| 构建方式 | 输入记录数 | 输出股票数 |",
        "|----------|-----------|-----------|",
        f"| 不使用 repaired | {len(records_without)} | {len(pool_without)} |",
        f"| 使用 repaired | {len(records_with)} | {len(pool_with)} |",
        f"| 差异 | +{len(records_with) - len(records_without)} | +{len(pool_with) - len(pool_without)} |",
        "",
        "## 二、新增股票（使用 repaired 后新增）",
        "",
        "| 股票代码 | 股票名称 | Attention Score | 出现天数 |",
        "|----------|----------|-----------------|----------|",
    ]

    for ticker in sorted(new_tickers):
        entry = tickers_with[ticker]
        report_lines.append(f"| {ticker} | {entry.name} | {entry.attention_score_20d:.1f} | {entry.appear_days_20d} |")

    if not new_tickers:
        report_lines.append("| （无） | | | |")

    report_lines.extend([
        "",
        "## 三、删除股票（使用 repaired 后消失）",
        "",
        "| 股票代码 | 股票名称 | 原 Attention Score | 原出现天数 |",
        "|----------|----------|-------------------|-----------|",
    ])

    for ticker in sorted(removed_tickers):
        entry = tickers_without[ticker]
        report_lines.append(f"| {ticker} | {entry.name} | {entry.attention_score_20d:.1f} | {entry.appear_days_20d} |")

    if not removed_tickers:
        report_lines.append("| （无） | | | |")

    report_lines.extend([
        "",
        "## 四、排名变化 Top 20（排名上升最多）",
        "",
        "| 排名 | 股票代码 | 股票名称 | 原排名 | 新排名 | 排名变化 | 原分数 | 新分数 |",
        "|------|----------|----------|--------|--------|----------|--------|--------|",
    ])

    for i, change in enumerate(rank_changes[:20], 1):
        report_lines.append(
            f"| {i} | {change['ticker']} | {change['name']} | "
            f"{change['old_rank']} | {change['new_rank']} | {change['change']:+d} | "
            f"{change['old_score']:.1f} | {change['new_score']:.1f} |"
        )

    report_lines.extend([
        "",
        "## 五、分数变化 Top 20（分数增加最多）",
        "",
        "| 排名 | 股票代码 | 股票名称 | 原分数 | 新分数 | 分数变化 |",
        "|------|----------|----------|--------|--------|----------|",
    ])

    for i, change in enumerate(score_changes[:20], 1):
        report_lines.append(
            f"| {i} | {change['ticker']} | {change['name']} | "
            f"{change['old_score']:.1f} | {change['new_score']:.1f} | {change['change']:+.1f} |"
        )

    report_lines.extend([
        "",
        "## 六、结论",
        "",
        f"- 使用 repaired legacy 后，Attention Pool 从 {len(pool_without)} 只股票增加到 {len(pool_with)} 只",
        f"- 新增 {len(new_tickers)} 只股票（来自修复后的记录）",
        f"- 删除 {len(removed_tickers)} 只股票",
        "- 修复数据作为增量合并，不会替代原有效数据",
        "- 同一天同一股票在不同平台的记录保留用于共振计算",
        "",
        "---",
        "",
        "**文档结束。**",
        "",
        f"> 本文档由 compare_attention_pool.py 自动生成于 {datetime.now().isoformat()}。",
    ])

    # Save report
    report_path = audit_dir / "attention_pool_compare_original_vs_repaired.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\nSaved comparison report to: {report_path}")

    # Print summary
    print(f"\n=== Comparison Summary ===")
    print(f"Without repaired: {len(pool_without)} stocks")
    print(f"With repaired: {len(pool_with)} stocks")
    print(f"New stocks: {len(new_tickers)}")
    print(f"Removed stocks: {len(removed_tickers)}")


if __name__ == "__main__":
    main()
