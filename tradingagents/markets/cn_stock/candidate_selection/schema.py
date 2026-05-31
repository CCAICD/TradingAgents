"""Candidate Selection data schemas.

These schemas define the structure for stock candidate selection in A-stock market.
Candidate Selection connects Theme Detection results with Attention Pool,
replacement rules, and risk flags to produce structured candidate lists.

NOTE: This is Phase 3D - data structure skeleton only.
No real stock selection algorithm, no trading recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# Enums
# ============================================================================


class CandidateSourceType(str, Enum):
    """Source of the candidate."""
    ATTENTION_POOL = "attention_pool"
    THEME_DETECTION = "theme_detection"
    OUT_OF_POOL_ALERT = "out_of_pool_alert"
    MANUAL_WATCHLIST = "manual_watchlist"
    REPLACEMENT_CANDIDATE = "replacement_candidate"
    UNKNOWN = "unknown"


class CandidateTradabilityFlag(str, Enum):
    """Tradability flags for a candidate."""
    MAIN_BOARD = "main_board"
    NON_MAIN_BOARD = "non_main_board"
    LIMIT_UP = "limit_up"
    HIGH_PRICE = "high_price"
    ST_OR_STAR_ST = "st_or_star_st"
    DELISTING_RISK = "delisting_risk"
    SUSPENDED = "suspended"
    LOW_LIQUIDITY = "low_liquidity"
    MISSING_PRICE_DATA = "missing_price_data"
    MISSING_ANNOUNCEMENT_DATA = "missing_announcement_data"
    MISSING_STRUCTURE_DATA = "missing_structure_data"
    UNKNOWN = "unknown"


class CandidateRiskLevel(str, Enum):
    """Risk level of a candidate."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class CandidateActionLabel(str, Enum):
    """Action label for a candidate. NOT buy/sell recommendations."""
    WATCH = "watch"
    WAIT_FOR_PULLBACK = "wait_for_pullback"
    WAIT_FOR_DIVERGENCE = "wait_for_divergence"
    AVOID = "avoid"
    RISK_UP = "risk_up"
    STRUCTURE_PENDING = "structure_pending"
    DATA_INSUFFICIENT = "data_insufficient"
    UNKNOWN = "unknown"


# ============================================================================
# Candidate schemas
# ============================================================================


@dataclass
class StockCandidate:
    """A stock candidate for potential participation."""

    ticker: str = ""
    name: str = ""
    theme_name: str = ""
    source_type: CandidateSourceType = CandidateSourceType.UNKNOWN
    source_reasons: List[str] = field(default_factory=list)
    board_type: str = ""
    is_main_board: Optional[bool] = None
    latest_price: Optional[float] = None
    is_limit_up: Optional[bool] = None
    attention_score_20d: Optional[float] = None
    theme_score: Optional[float] = None
    candidate_score: Optional[float] = None
    tradability_flags: List[CandidateTradabilityFlag] = field(default_factory=list)
    risk_level: CandidateRiskLevel = CandidateRiskLevel.UNKNOWN
    action_label: CandidateActionLabel = CandidateActionLabel.UNKNOWN
    evidence: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blocking_reasons: List[str] = field(default_factory=list)
    requires_replacement: bool = False
    replacement_reason: str = ""
    data_statuses: List[Any] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "theme_name": self.theme_name,
            "source_type": self.source_type.value,
            "source_reasons": self.source_reasons,
            "board_type": self.board_type,
            "is_main_board": self.is_main_board,
            "latest_price": self.latest_price,
            "is_limit_up": self.is_limit_up,
            "attention_score_20d": self.attention_score_20d,
            "theme_score": self.theme_score,
            "candidate_score": self.candidate_score,
            "tradability_flags": [f.value for f in self.tradability_flags],
            "risk_level": self.risk_level.value,
            "action_label": self.action_label.value,
            "evidence": self.evidence,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "requires_replacement": self.requires_replacement,
            "replacement_reason": self.replacement_reason,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StockCandidate":
        return cls(
            ticker=d.get("ticker", ""),
            name=d.get("name", ""),
            theme_name=d.get("theme_name", ""),
            source_type=CandidateSourceType(d.get("source_type", "unknown")),
            source_reasons=d.get("source_reasons", []),
            board_type=d.get("board_type", ""),
            is_main_board=d.get("is_main_board"),
            latest_price=d.get("latest_price"),
            is_limit_up=d.get("is_limit_up"),
            attention_score_20d=d.get("attention_score_20d"),
            theme_score=d.get("theme_score"),
            candidate_score=d.get("candidate_score"),
            tradability_flags=[CandidateTradabilityFlag(f) for f in d.get("tradability_flags", [])],
            risk_level=CandidateRiskLevel(d.get("risk_level", "unknown")),
            action_label=CandidateActionLabel(d.get("action_label", "unknown")),
            evidence=d.get("evidence", []),
            warnings=d.get("warnings", []),
            blocking_reasons=d.get("blocking_reasons", []),
            requires_replacement=d.get("requires_replacement", False),
            replacement_reason=d.get("replacement_reason", ""),
        )


@dataclass
class ReplacementCandidate:
    """A replacement candidate for an unsuitable original candidate."""

    original_ticker: str = ""
    original_name: str = ""
    replacement_ticker: str = ""
    replacement_name: str = ""
    theme_name: str = ""
    replacement_reason: str = ""
    why_original_not_suitable: str = ""
    evidence: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    data_statuses: List[Any] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "original_ticker": self.original_ticker,
            "original_name": self.original_name,
            "replacement_ticker": self.replacement_ticker,
            "replacement_name": self.replacement_name,
            "theme_name": self.theme_name,
            "replacement_reason": self.replacement_reason,
            "why_original_not_suitable": self.why_original_not_suitable,
            "evidence": self.evidence,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ReplacementCandidate":
        return cls(
            original_ticker=d.get("original_ticker", ""),
            original_name=d.get("original_name", ""),
            replacement_ticker=d.get("replacement_ticker", ""),
            replacement_name=d.get("replacement_name", ""),
            theme_name=d.get("theme_name", ""),
            replacement_reason=d.get("replacement_reason", ""),
            why_original_not_suitable=d.get("why_original_not_suitable", ""),
            evidence=d.get("evidence", []),
            warnings=d.get("warnings", []),
        )


@dataclass
class OutOfPoolHighConvictionCandidate:
    """A high-conviction candidate from outside the Attention Pool.

    NOTE: This is a hint/observation only, NOT a participation recommendation.
    """

    ticker: str = ""
    name: str = ""
    theme_name: str = ""
    why_not_in_attention_pool: str = ""
    why_still_worth_tracking: str = ""
    evidence: List[str] = field(default_factory=list)
    requires_replacement: bool = False
    replacement_candidate: Optional[ReplacementCandidate] = None
    warnings: List[str] = field(default_factory=list)
    risk_level: CandidateRiskLevel = CandidateRiskLevel.UNKNOWN
    action_label: CandidateActionLabel = CandidateActionLabel.WATCH

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "theme_name": self.theme_name,
            "why_not_in_attention_pool": self.why_not_in_attention_pool,
            "why_still_worth_tracking": self.why_still_worth_tracking,
            "evidence": self.evidence,
            "requires_replacement": self.requires_replacement,
            "replacement_candidate": self.replacement_candidate.to_dict() if self.replacement_candidate else None,
            "warnings": self.warnings,
            "risk_level": self.risk_level.value,
            "action_label": self.action_label.value,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "OutOfPoolHighConvictionCandidate":
        replacement = None
        if d.get("replacement_candidate"):
            replacement = ReplacementCandidate.from_dict(d["replacement_candidate"])

        return cls(
            ticker=d.get("ticker", ""),
            name=d.get("name", ""),
            theme_name=d.get("theme_name", ""),
            why_not_in_attention_pool=d.get("why_not_in_attention_pool", ""),
            why_still_worth_tracking=d.get("why_still_worth_tracking", ""),
            evidence=d.get("evidence", []),
            requires_replacement=d.get("requires_replacement", False),
            replacement_candidate=replacement,
            warnings=d.get("warnings", []),
            risk_level=CandidateRiskLevel(d.get("risk_level", "unknown")),
            action_label=CandidateActionLabel(d.get("action_label", "watch")),
        )


# ============================================================================
# Input / Output
# ============================================================================


@dataclass
class ManualConstraints:
    """Manual constraints for candidate selection."""

    prefer_main_board: bool = True
    high_price_threshold: float = 120.0
    avoid_limit_up: bool = True
    allow_non_main_board: bool = False
    max_single_stock_price: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "prefer_main_board": self.prefer_main_board,
            "high_price_threshold": self.high_price_threshold,
            "avoid_limit_up": self.avoid_limit_up,
            "allow_non_main_board": self.allow_non_main_board,
            "max_single_stock_price": self.max_single_stock_price,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ManualConstraints":
        return cls(
            prefer_main_board=d.get("prefer_main_board", True),
            high_price_threshold=d.get("high_price_threshold", 120.0),
            avoid_limit_up=d.get("avoid_limit_up", True),
            allow_non_main_board=d.get("allow_non_main_board", False),
            max_single_stock_price=d.get("max_single_stock_price"),
        )


@dataclass
class CandidateSelectionInput:
    """Input for Candidate Selection."""

    trade_date: str = ""
    scan_time: Optional[datetime] = None
    theme_detection_result: Optional[Any] = None     # ThemeDetectionResult
    attention_pool_items: List[Any] = field(default_factory=list)  # AttentionPoolEntry list
    market_scan_result: Optional[Any] = None         # MarketWideScanResult
    data_freshness_result: Optional[Any] = None      # ReportFreshnessResult
    manual_constraints: ManualConstraints = field(default_factory=ManualConstraints)

    def to_dict(self) -> dict:
        return {
            "trade_date": self.trade_date,
            "scan_time": self.scan_time.isoformat() if self.scan_time else None,
            "theme_detection_result": self.theme_detection_result.to_dict() if self.theme_detection_result and hasattr(self.theme_detection_result, "to_dict") else None,
            "attention_pool_items": [a.to_dict() if hasattr(a, "to_dict") else a for a in self.attention_pool_items],
            "market_scan_result": self.market_scan_result.to_dict() if self.market_scan_result and hasattr(self.market_scan_result, "to_dict") else None,
            "data_freshness_result": self.data_freshness_result.to_dict() if self.data_freshness_result and hasattr(self.data_freshness_result, "to_dict") else None,
            "manual_constraints": self.manual_constraints.to_dict(),
        }


@dataclass
class CandidateSelectionResult:
    """Result of Candidate Selection."""

    trade_date: str = ""
    scan_time: Optional[datetime] = None
    candidates_by_theme: Dict[str, List[StockCandidate]] = field(default_factory=dict)
    attention_pool_priority_candidates: List[StockCandidate] = field(default_factory=list)
    replacement_candidates: List[ReplacementCandidate] = field(default_factory=list)
    out_of_pool_high_conviction_candidates: List[OutOfPoolHighConvictionCandidate] = field(default_factory=list)
    blocked_candidates: List[StockCandidate] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blocking_reasons: List[str] = field(default_factory=list)
    can_continue_to_report: bool = True
    data_freshness_result: Optional[Any] = None

    def to_dict(self) -> dict:
        return {
            "trade_date": self.trade_date,
            "scan_time": self.scan_time.isoformat() if self.scan_time else None,
            "candidates_by_theme": {
                theme: [c.to_dict() for c in candidates]
                for theme, candidates in self.candidates_by_theme.items()
            },
            "attention_pool_priority_candidates": [c.to_dict() for c in self.attention_pool_priority_candidates],
            "replacement_candidates": [r.to_dict() for r in self.replacement_candidates],
            "out_of_pool_high_conviction_candidates": [o.to_dict() for o in self.out_of_pool_high_conviction_candidates],
            "blocked_candidates": [c.to_dict() for c in self.blocked_candidates],
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "can_continue_to_report": self.can_continue_to_report,
            "data_freshness_result": self.data_freshness_result.to_dict() if self.data_freshness_result and hasattr(self.data_freshness_result, "to_dict") else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CandidateSelectionResult":
        scan_time = None
        if d.get("scan_time"):
            try:
                scan_time = datetime.fromisoformat(d["scan_time"])
            except (ValueError, TypeError):
                pass

        candidates_by_theme = {}
        for theme, candidates in d.get("candidates_by_theme", {}).items():
            candidates_by_theme[theme] = [StockCandidate.from_dict(c) for c in candidates]

        return cls(
            trade_date=d.get("trade_date", ""),
            scan_time=scan_time,
            candidates_by_theme=candidates_by_theme,
            attention_pool_priority_candidates=[StockCandidate.from_dict(c) for c in d.get("attention_pool_priority_candidates", [])],
            replacement_candidates=[ReplacementCandidate.from_dict(r) for r in d.get("replacement_candidates", [])],
            out_of_pool_high_conviction_candidates=[OutOfPoolHighConvictionCandidate.from_dict(o) for o in d.get("out_of_pool_high_conviction_candidates", [])],
            blocked_candidates=[StockCandidate.from_dict(c) for c in d.get("blocked_candidates", [])],
            warnings=d.get("warnings", []),
            blocking_reasons=d.get("blocking_reasons", []),
            can_continue_to_report=d.get("can_continue_to_report", True),
        )
