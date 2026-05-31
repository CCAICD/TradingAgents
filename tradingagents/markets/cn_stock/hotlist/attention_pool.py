"""Attention Pool builder.

Builds the Attention Pool from structured hotlist records using a configurable
scoring formula. This is a v0.1 implementation that will be refined over time.

IMPORTANT: Attention Pool is a "market attention pool", not a "buyable pool".
It does NOT filter by board type, price, or tradability.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from .schema import (
    AttentionPoolEntry,
    AttentionScoreConfig,
    HotlistRecord,
    ScoreBreakdown,
    ScoreEvidence,
)


def _get_sorted_trade_dates(records: List[HotlistRecord]) -> List[str]:
    """Get unique trade dates sorted descending (newest first)."""
    dates = set()
    for r in records:
        if r.trade_date and r.parse_status in ("valid", "warning"):
            dates.add(r.trade_date)
    return sorted(dates, reverse=True)


def _compute_consecutive_days(
    ticker: str,
    records_by_ticker: Dict[str, List[HotlistRecord]],
    window_dates: List[str],
) -> int:
    """Compute consecutive days a ticker appears from the latest date."""
    ticker_records = records_by_ticker.get(ticker, [])
    record_dates = {r.trade_date for r in ticker_records if r.parse_status in ("valid", "warning")}

    consecutive = 0
    for date in window_dates:
        if date in record_dates:
            consecutive += 1
        else:
            break
    return consecutive


def build_attention_pool(
    records: List[HotlistRecord],
    config: Optional[AttentionScoreConfig] = None,
    window_trade_days: Optional[int] = None,
    include_breakdown: bool = True,
) -> List[AttentionPoolEntry]:
    """Build Attention Pool from hotlist records.

    Args:
        records: List of hotlist records (from manual input and/or legacy import)
        config: Scoring configuration (uses defaults if None)
        window_trade_days: Override for WINDOW_TRADE_DAYS
        include_breakdown: Whether to include score breakdown and evidence

    Returns:
        List of AttentionPoolEntry sorted by attention_score_20d descending
    """
    if config is None:
        config = AttentionScoreConfig()
    if window_trade_days is not None:
        config.WINDOW_TRADE_DAYS = window_trade_days

    # Filter valid records only
    valid_records = [r for r in records if r.parse_status in ("valid", "warning") and r.ticker]

    if not valid_records:
        return []

    # Get sorted trade dates (descending)
    all_dates = _get_sorted_trade_dates(valid_records)
    window_dates = all_dates[: config.WINDOW_TRADE_DAYS]

    if not window_dates:
        return []

    # Map date to age_index (0 = newest)
    date_to_age = {d: i for i, d in enumerate(window_dates)}

    # Group records by ticker
    records_by_ticker: Dict[str, List[HotlistRecord]] = defaultdict(list)
    for r in valid_records:
        if r.trade_date in date_to_age:
            records_by_ticker[r.ticker].append(r)

    # Compute scores
    pool_entries: List[AttentionPoolEntry] = []

    for ticker, ticker_records in records_by_ticker.items():
        # Group by date
        records_by_date: Dict[str, List[HotlistRecord]] = defaultdict(list)
        for r in ticker_records:
            records_by_date[r.trade_date].append(r)

        total_score = 0.0
        total_resonance_bonus = 0.0
        appear_days = 0
        all_sources: Set[str] = set()
        all_source_projects: Set[str] = set()
        all_ranks: List[int] = []
        latest_date = ""
        latest_rank: Optional[int] = None
        latest_sources: List[str] = []
        first_seen_date = ""
        warnings: List[str] = []
        raw_count = 0

        # For explainability
        appeared_dates: List[str] = []
        best_rank_records: List[dict] = []
        source_frequency: Dict[str, int] = defaultdict(int)
        daily_source_counts: Dict[str, int] = {}

        for date in window_dates:
            date_records = records_by_date.get(date, [])
            if not date_records:
                continue

            appear_days += 1
            appeared_dates.append(date)
            age_index = date_to_age[date]
            recency_weight = 0.5 ** (age_index / config.HALF_LIFE_DAYS)

            # Track first seen
            if not first_seen_date or date < first_seen_date:
                first_seen_date = date

            # Track latest
            if not latest_date or date > latest_date:
                latest_date = date

            # Compute daily scores
            daily_sources: Set[str] = set()
            for r in date_records:
                raw_count += 1
                all_sources.add(r.source)
                all_source_projects.add(r.source_project)
                daily_sources.add(r.source)
                source_frequency[r.source] += 1

                if r.rank is not None:
                    all_ranks.append(r.rank)
                    rank_score = max(1, config.RANK_TOP_N + 1 - r.rank)
                    total_score += rank_score * recency_weight

                    # Track best rank records
                    if not best_rank_records or r.rank < best_rank_records[0].get("rank", 999):
                        best_rank_records = [{
                            "date": date,
                            "rank": r.rank,
                            "source": r.source,
                            "ticker": r.ticker,
                            "name": r.name,
                        }]
                    elif r.rank == best_rank_records[0].get("rank"):
                        best_rank_records.append({
                            "date": date,
                            "rank": r.rank,
                            "source": r.source,
                            "ticker": r.ticker,
                            "name": r.name,
                        })
                else:
                    warnings.append(f"Missing rank on {date}")

            # Update latest info
            if date == latest_date:
                latest_sources = list(daily_sources)
                latest_ranks = [r.rank for r in date_records if r.rank is not None]
                if latest_ranks:
                    latest_rank = min(latest_ranks)

            # Daily resonance bonus
            daily_source_count = len(daily_sources)
            daily_source_counts[date] = daily_source_count
            if daily_source_count > 1:
                resonance_bonus = (
                    (daily_source_count - 1)
                    * config.RESONANCE_BONUS_PER_EXTRA_SOURCE
                    * recency_weight
                )
                total_resonance_bonus += resonance_bonus

        # Consecutive days bonus
        consecutive = _compute_consecutive_days(ticker, records_by_ticker, window_dates)
        consecutive_bonus = min(consecutive, config.MAX_CONSECUTIVE_BONUS_DAYS) * config.CONSECUTIVE_BONUS_PER_DAY

        # Final score
        attention_score = total_score + total_resonance_bonus + consecutive_bonus

        # Compute rank statistics
        best_rank = min(all_ranks) if all_ranks else None
        avg_rank = sum(all_ranks) / len(all_ranks) if all_ranks else None

        # Get name (prefer non-empty)
        name = ""
        for r in ticker_records:
            if r.name:
                name = r.name
                break

        # Get board type (prefer main_board if any record says so)
        is_main_board = None
        board_type = "unknown"
        for r in ticker_records:
            if r.is_main_board is True:
                is_main_board = True
                board_type = r.board_type
                break
            elif r.is_main_board is False:
                is_main_board = False
                board_type = r.board_type

        # Build breakdown and evidence if requested
        score_breakdown = None
        evidence = None
        if include_breakdown:
            score_breakdown = ScoreBreakdown(
                rank_score_sum=total_score,
                resonance_bonus_sum=total_resonance_bonus,
                consecutive_bonus=consecutive_bonus,
                recency_weighted_score=total_score + total_resonance_bonus,
                final_score=attention_score,
            )
            evidence = ScoreEvidence(
                appeared_dates=appeared_dates,
                latest_sources=latest_sources,
                best_rank_records=best_rank_records,
                source_frequency=dict(source_frequency),
                daily_source_counts=daily_source_counts,
            )

        entry = AttentionPoolEntry(
            ticker=ticker,
            name=name,
            attention_score_20d=attention_score,
            appear_days_20d=appear_days,
            consecutive_days=consecutive,
            latest_trade_date=latest_date,
            latest_rank=latest_rank,
            best_rank_20d=best_rank,
            avg_rank_20d=avg_rank,
            source_count_20d=len(all_sources),
            sources_20d=list(all_sources),
            latest_sources=latest_sources,
            first_seen_date_20d=first_seen_date,
            is_main_board=is_main_board,
            board_type=board_type,
            source_projects=list(all_source_projects),
            data_warnings=warnings,
            raw_record_count=raw_count,
            score_breakdown=score_breakdown,
            evidence=evidence,
        )
        pool_entries.append(entry)

    # Sort by score descending
    pool_entries.sort(key=lambda e: e.attention_score_20d, reverse=True)

    return pool_entries


def generate_build_summary(
    pool_entries: List[AttentionPoolEntry],
    records: List[HotlistRecord],
    config: AttentionScoreConfig,
    include_legacy: bool,
    include_repaired: bool = False,
    repaired_count: int = 0,
    unresolved_count: int = 0,
    conflict_count: int = 0,
    dedup_count: int = 0,
) -> str:
    """Generate a markdown summary of the Attention Pool build.

    Args:
        pool_entries: Built Attention Pool entries
        records: Input records
        config: Scoring configuration used
        include_legacy: Whether legacy data was included
        include_repaired: Whether repaired legacy data was included
        repaired_count: Number of repaired records
        unresolved_count: Number of unresolved records
        conflict_count: Number of conflict records
        dedup_count: Number of deduplicated records

    Returns:
        Markdown summary string
    """
    valid_records = [r for r in records if r.parse_status in ("valid", "warning")]
    invalid_records = [r for r in records if r.parse_status == "invalid"]

    # Date range
    dates = sorted(set(r.trade_date for r in valid_records if r.trade_date))
    date_range = f"{dates[0]} to {dates[-1]}" if dates else "N/A"

    # Platform counts
    platform_counts: Dict[str, int] = defaultdict(int)
    for r in valid_records:
        platform_counts[r.source] += 1

    # Board type counts
    board_counts: Dict[str, int] = defaultdict(int)
    for e in pool_entries:
        board_counts[e.board_type] += 1

    # Main board count
    main_board_count = sum(1 for e in pool_entries if e.is_main_board is True)
    non_main_board_count = sum(1 for e in pool_entries if e.is_main_board is False)
    unknown_board_count = sum(1 for e in pool_entries if e.is_main_board is None)

    lines = [
        "# Attention Pool Build Summary",
        "",
        f"> Build time: {datetime.now().isoformat()}",
        "",
        "---",
        "",
        "## 一、构建概览",
        "",
        "| 项目 | 数值 |",
        "|------|------|",
        f"| 输入记录数 | {len(records)} |",
        f"| 有效记录数 | {len(valid_records)} |",
        f"| 无效记录数 | {len(invalid_records)} |",
        f"| 日期范围 | {date_range} |",
        f"| Attention Pool 股票数 | {len(pool_entries)} |",
        f"| 是否包含 legacy 数据 | {'是' if include_legacy else '否'} |",
        f"| 是否包含 repaired 数据 | {'是' if include_repaired else '否'} |",
        f"| 窗口天数 | {config.WINDOW_TRADE_DAYS} |",
    ]

    if include_repaired:
        lines.extend([
            "",
            "## 二、修复统计",
            "",
            "| 项目 | 数值 |",
            "|------|------|",
            f"| 修复成功记录数 | {repaired_count} |",
            f"| 无法修复记录数 | {unresolved_count} |",
            f"| 冲突记录数 | {conflict_count} |",
            f"| 去重记录数 | {dedup_count} |",
        ])

    lines.extend([
        "",
        "## 三、平台覆盖",
        "",
        "| 平台 | 记录数 |",
        "|------|--------|",
    ])

    for platform, count in sorted(platform_counts.items()):
        lines.append(f"| {platform} | {count} |")

    lines.extend([
        "",
        "## 四、板块分布",
        "",
        "| 类型 | 股票数 |",
        "|------|--------|",
        f"| 主板 | {main_board_count} |",
        f"| 非主板 | {non_main_board_count} |",
        f"| 未知 | {unknown_board_count} |",
        "",
        "### 板块类型明细",
        "",
        "| 板块类型 | 股票数 |",
        "|----------|--------|",
    ])

    for board, count in sorted(board_counts.items()):
        lines.append(f"| {board} | {count} |")

    lines.extend([
        "",
        "## 五、Attention Score 配置",
        "",
        "| 参数 | 值 |",
        "|------|-----|",
        f"| RANK_TOP_N | {config.RANK_TOP_N} |",
        f"| HALF_LIFE_DAYS | {config.HALF_LIFE_DAYS} |",
        f"| RESONANCE_BONUS_PER_EXTRA_SOURCE | {config.RESONANCE_BONUS_PER_EXTRA_SOURCE} |",
        f"| CONSECUTIVE_BONUS_PER_DAY | {config.CONSECUTIVE_BONUS_PER_DAY} |",
        f"| MAX_CONSECUTIVE_BONUS_DAYS | {config.MAX_CONSECUTIVE_BONUS_DAYS} |",
        f"| WINDOW_TRADE_DAYS | {config.WINDOW_TRADE_DAYS} |",
        "",
        "## 六、Top 20 Attention Pool",
        "",
        "| 排名 | 股票代码 | 股票名称 | Attention Score | 出现天数 | 连续天数 | 主板 |",
        "|------|----------|----------|-----------------|----------|----------|------|",
    ])

    for i, entry in enumerate(pool_entries[:20], 1):
        board_str = "Y" if entry.is_main_board else ("N" if entry.is_main_board is False else "?")
        lines.append(
            f"| {i} | {entry.ticker} | {entry.name} | "
            f"{entry.attention_score_20d:.1f} | {entry.appear_days_20d} | "
            f"{entry.consecutive_days} | {board_str} |"
        )

    lines.extend([
        "",
        "## 七、注意事项",
        "",
        "- Attention Pool 是市场注意力池，不是用户可买池",
        "- 非主板股票未被剔除，它们可作为主线强度证据",
        "- 本轮未接入实时行情，不提供价格、涨停、成交额等信息",
        "- Attention Score v0.1 公式为初版，后续会调整",
        "- board_type 为离线粗略推断，不能替代实时交易资格判断",
        "",
        "---",
        "",
        "**文档结束。**",
        "",
        f"> 本文档由 build_attention_pool.py 自动生成于 {datetime.now().isoformat()}。",
    ])

    return "\n".join(lines)


def generate_top50_explain(
    pool_entries: List[AttentionPoolEntry],
) -> Tuple[str, list]:
    """Generate explanation for top 50 Attention Pool entries.

    Args:
        pool_entries: Built Attention Pool entries

    Returns:
        Tuple of (markdown_string, json_list)
    """
    top50 = pool_entries[:50]
    json_list = []
    lines = [
        "# Attention Pool Top 50 评分解释",
        "",
        f"> 生成时间：{datetime.now().isoformat()}",
        "",
        "---",
        "",
    ]

    for i, entry in enumerate(top50, 1):
        breakdown = entry.score_breakdown
        evidence = entry.evidence

        lines.append(f"## {i}. {entry.ticker} ({entry.name})")
        lines.append("")
        lines.append(f"**Attention Score: {entry.attention_score_20d:.2f}**")
        lines.append("")

        if breakdown:
            lines.append("### 评分分解")
            lines.append("")
            lines.append(f"- 排名分数合计 (rank_score_sum): {breakdown.rank_score_sum:.2f}")
            lines.append(f"- 多平台共振加分 (resonance_bonus_sum): {breakdown.resonance_bonus_sum:.2f}")
            lines.append(f"- 连续上榜加分 (consecutive_bonus): {breakdown.consecutive_bonus:.2f}")
            lines.append(f"- 最终分数 (final_score): {breakdown.final_score:.2f}")
            lines.append("")

        if evidence:
            lines.append("### 证据")
            lines.append("")
            lines.append(f"- 出现日期: {', '.join(evidence.appeared_dates)}")
            lines.append(f"- 最新来源: {', '.join(evidence.latest_sources)}")
            if evidence.best_rank_records:
                lines.append(f"- 最佳排名记录: {evidence.best_rank_records[0]}")
            lines.append(f"- 来源频率: {evidence.source_frequency}")
            lines.append(f"- 每日来源数: {evidence.daily_source_counts}")
            lines.append("")

        # Special explanation for high-score single-day entries
        if entry.appear_days_20d == 1 and entry.attention_score_20d > 50:
            lines.append("**注意:** 该股票仅出现 1 天但分数较高，可能因为：")
            lines.append("- 单日高排名（如排名第 1）")
            lines.append("- 多平台共振（同一天出现在多个平台）")
            lines.append("- 这不代表持续热度，需要后续观察")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Build JSON entry
        json_entry = {
            "rank": i,
            "ticker": entry.ticker,
            "name": entry.name,
            "attention_score_20d": round(entry.attention_score_20d, 2),
            "appear_days_20d": entry.appear_days_20d,
            "consecutive_days": entry.consecutive_days,
        }
        if breakdown:
            json_entry["score_breakdown"] = breakdown.to_dict()
        if evidence:
            json_entry["evidence"] = evidence.to_dict()
        json_list.append(json_entry)

    return "\n".join(lines), json_list
