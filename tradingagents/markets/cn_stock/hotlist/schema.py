"""Data schemas for CN Stock hotlist and Attention Pool.

These schemas define the structure for hotlist records and attention pool entries.
They are used for A-stock market analysis only and should not affect US stock
or crypto functionality.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


# Valid platform sources
VALID_SOURCES = {"同花顺", "东方财富", "雪球", "通达信"}


@dataclass
class HotlistRecord:
    """A single hotlist record from manual input or legacy import."""

    trade_date: str                          # YYYY-MM-DD
    source: str                              # Platform name (同花顺/东方财富/雪球/通达信)
    rank: Optional[int] = None               # Position in the hotlist (1-based)
    ticker: str = ""                         # Stock code with suffix (e.g., 600519.SH)
    name: str = ""                           # Stock name
    board_type: str = "unknown"              # main_board/gem_star/unknown etc.
    is_main_board: Optional[bool] = None     # True if main board
    raw_line: str = ""                       # Original text line
    parse_status: str = "valid"              # valid/warning/invalid
    parse_warnings: List[str] = field(default_factory=list)
    source_project: str = "manual_input"     # manual_input or tradingagents-old
    original_path: str = ""                  # Source file path
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "trade_date": self.trade_date,
            "source": self.source,
            "rank": self.rank,
            "ticker": self.ticker,
            "name": self.name,
            "board_type": self.board_type,
            "is_main_board": self.is_main_board,
            "raw_line": self.raw_line,
            "parse_status": self.parse_status,
            "parse_warnings": self.parse_warnings,
            "source_project": self.source_project,
            "original_path": self.original_path,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "HotlistRecord":
        """Create from dictionary."""
        return cls(
            trade_date=d.get("trade_date", ""),
            source=d.get("source", ""),
            rank=d.get("rank"),
            ticker=d.get("ticker", ""),
            name=d.get("name", ""),
            board_type=d.get("board_type", "unknown"),
            is_main_board=d.get("is_main_board"),
            raw_line=d.get("raw_line", ""),
            parse_status=d.get("parse_status", "valid"),
            parse_warnings=d.get("parse_warnings", []),
            source_project=d.get("source_project", "manual_input"),
            original_path=d.get("original_path", ""),
            created_at=d.get("created_at", ""),
        )


@dataclass
class AttentionScoreConfig:
    """Configuration for Attention Score calculation (v0.1)."""

    RANK_TOP_N: int = 20
    HALF_LIFE_DAYS: int = 10
    RESONANCE_BONUS_PER_EXTRA_SOURCE: float = 5.0
    CONSECUTIVE_BONUS_PER_DAY: float = 3.0
    MAX_CONSECUTIVE_BONUS_DAYS: int = 5
    WINDOW_TRADE_DAYS: int = 20


@dataclass
class ScoreBreakdown:
    """Breakdown of Attention Score calculation."""

    rank_score_sum: float = 0.0
    resonance_bonus_sum: float = 0.0
    consecutive_bonus: float = 0.0
    recency_weighted_score: float = 0.0
    final_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "rank_score_sum": round(self.rank_score_sum, 2),
            "resonance_bonus_sum": round(self.resonance_bonus_sum, 2),
            "consecutive_bonus": round(self.consecutive_bonus, 2),
            "recency_weighted_score": round(self.recency_weighted_score, 2),
            "final_score": round(self.final_score, 2),
        }


@dataclass
class ScoreEvidence:
    """Evidence supporting the Attention Score."""

    appeared_dates: List[str] = field(default_factory=list)
    latest_sources: List[str] = field(default_factory=list)
    best_rank_records: List[dict] = field(default_factory=list)
    source_frequency: dict = field(default_factory=dict)
    daily_source_counts: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "appeared_dates": self.appeared_dates,
            "latest_sources": self.latest_sources,
            "best_rank_records": self.best_rank_records,
            "source_frequency": self.source_frequency,
            "daily_source_counts": self.daily_source_counts,
        }


@dataclass
class AttentionPoolEntry:
    """A single entry in the Attention Pool."""

    ticker: str
    name: str
    attention_score_20d: float
    appear_days_20d: int
    consecutive_days: int
    latest_trade_date: str
    latest_rank: Optional[int]
    best_rank_20d: Optional[int]
    avg_rank_20d: Optional[float]
    source_count_20d: int
    sources_20d: List[str]
    latest_sources: List[str]
    first_seen_date_20d: str
    is_main_board: Optional[bool]
    board_type: str
    source_projects: List[str]
    data_warnings: List[str]
    raw_record_count: int
    score_breakdown: Optional[ScoreBreakdown] = None
    evidence: Optional[ScoreEvidence] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "ticker": self.ticker,
            "name": self.name,
            "attention_score_20d": round(self.attention_score_20d, 2),
            "appear_days_20d": self.appear_days_20d,
            "consecutive_days": self.consecutive_days,
            "latest_trade_date": self.latest_trade_date,
            "latest_rank": self.latest_rank,
            "best_rank_20d": self.best_rank_20d,
            "avg_rank_20d": round(self.avg_rank_20d, 2) if self.avg_rank_20d is not None else None,
            "source_count_20d": self.source_count_20d,
            "sources_20d": sorted(self.sources_20d),
            "latest_sources": sorted(self.latest_sources),
            "first_seen_date_20d": self.first_seen_date_20d,
            "is_main_board": self.is_main_board,
            "board_type": self.board_type,
            "source_projects": sorted(set(self.source_projects)),
            "data_warnings": self.data_warnings,
            "raw_record_count": self.raw_record_count,
        }
        if self.score_breakdown:
            result["score_breakdown"] = self.score_breakdown.to_dict()
        if self.evidence:
            result["evidence"] = self.evidence.to_dict()
        return result
