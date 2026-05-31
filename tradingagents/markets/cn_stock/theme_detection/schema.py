"""Theme Detection data schemas.

These schemas define the structure for theme/mainline detection in A-stock market.
Theme Detection connects Market-Wide Scan results with Attention Pool to generate
theme candidates for the decision pipeline.

NOTE: This is Phase 3C - data structure skeleton only.
No real theme detection algorithm, no trading recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# Enums
# ============================================================================


class ThemeLevel(str, Enum):
    """Theme level classification."""
    S = "S"                  # 最强主线
    A = "A"                  # 强主线
    B = "B"                  # 观察主线
    C = "C"                  # 一日游/伪主线
    UNKNOWN = "unknown"      # 数据不足


class ThemeStatus(str, Enum):
    """Theme lifecycle status."""
    EMERGING = "emerging"                    # 新兴主题
    STRENGTHENING = "strengthening"          # 加强中
    MAIN_RISING = "main_rising"             # 主升阶段
    FIRST_DIVERGENCE = "first_divergence"   # 第一次分歧
    ROTATING = "rotating"                   # 轮动中
    WEAKENING = "weakening"                 # 走弱中
    FADING = "fading"                       # 退潮中
    ONE_DAY_NOISE = "one_day_noise"         # 一日游
    UNKNOWN = "unknown"


class ThemeEvidenceType(str, Enum):
    """Type of theme evidence."""
    SECTOR_STRENGTH = "sector_strength"                    # 板块强度
    LIMIT_UP_CLUSTER = "limit_up_cluster"                  # 涨停聚集
    TURNOVER_EXPANSION = "turnover_expansion"              # 成交额放大
    ATTENTION_POOL_OVERLAP = "attention_pool_overlap"      # Attention Pool 重叠
    LEADER_STOCK_STRENGTH = "leader_stock_strength"        # 龙头股强度
    POLICY_OR_NEWS_CATALYST = "policy_or_news_catalyst"    # 政策/新闻催化
    ANNOUNCEMENT_CATALYST = "announcement_catalyst"        # 公告催化
    OUT_OF_POOL_SIGNAL = "out_of_pool_signal"              # 池外信号
    RISK_WARNING = "risk_warning"                          # 风险警告


# ============================================================================
# Evidence
# ============================================================================


@dataclass
class ThemeEvidence:
    """Evidence supporting or weakening a theme candidate."""

    evidence_type: ThemeEvidenceType
    description: str = ""
    source: str = ""                           # Data source
    related_sectors: List[str] = field(default_factory=list)
    related_stocks: List[str] = field(default_factory=list)
    score_contribution: float = 0.0            # Score contribution from this evidence
    confidence: float = 0.0                    # Confidence level (0-1)
    as_of_time: Optional[datetime] = None
    data_status: str = ""                      # fresh/stale/missing/failed

    def to_dict(self) -> dict:
        return {
            "evidence_type": self.evidence_type.value,
            "description": self.description,
            "source": self.source,
            "related_sectors": self.related_sectors,
            "related_stocks": self.related_stocks,
            "score_contribution": round(self.score_contribution, 2),
            "confidence": round(self.confidence, 2),
            "as_of_time": self.as_of_time.isoformat() if self.as_of_time else None,
            "data_status": self.data_status,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ThemeEvidence":
        as_of_time = None
        if d.get("as_of_time"):
            try:
                as_of_time = datetime.fromisoformat(d["as_of_time"])
            except (ValueError, TypeError):
                pass

        return cls(
            evidence_type=ThemeEvidenceType(d.get("evidence_type", "sector_strength")),
            description=d.get("description", ""),
            source=d.get("source", ""),
            related_sectors=d.get("related_sectors", []),
            related_stocks=d.get("related_stocks", []),
            score_contribution=d.get("score_contribution", 0.0),
            confidence=d.get("confidence", 0.0),
            as_of_time=as_of_time,
            data_status=d.get("data_status", ""),
        )


# ============================================================================
# Theme Candidate
# ============================================================================


@dataclass
class ThemeCandidate:
    """A candidate theme/mainline identified by Theme Detection."""

    theme_name: str = ""                       # Theme name, e.g., "半导体"
    theme_aliases: List[str] = field(default_factory=list)  # Alternative names
    related_sectors: List[str] = field(default_factory=list)  # Related sector names/codes
    core_stocks: List[str] = field(default_factory=list)     # Core/leading stocks
    trend_mid_caps: List[str] = field(default_factory=list)  # Trend mid-cap stocks
    elastic_stocks: List[str] = field(default_factory=list)  # Elastic/high-beta stocks
    replacement_candidates: List[str] = field(default_factory=list)  # Replacement candidates
    attention_pool_stocks: List[str] = field(default_factory=list)   # Stocks in Attention Pool
    out_of_pool_stocks: List[str] = field(default_factory=list)     # Stocks not in Attention Pool
    evidence: List[ThemeEvidence] = field(default_factory=list)
    theme_score: float = 0.0                   # Total theme score
    theme_level: ThemeLevel = ThemeLevel.UNKNOWN
    theme_status: ThemeStatus = ThemeStatus.UNKNOWN
    is_new_theme: bool = False                 # Is this a new/emerging theme
    is_one_day_noise_candidate: bool = False   # Likely one-day noise
    warnings: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)  # Risk warnings

    def to_dict(self) -> dict:
        return {
            "theme_name": self.theme_name,
            "theme_aliases": self.theme_aliases,
            "related_sectors": self.related_sectors,
            "core_stocks": self.core_stocks,
            "trend_mid_caps": self.trend_mid_caps,
            "elastic_stocks": self.elastic_stocks,
            "replacement_candidates": self.replacement_candidates,
            "attention_pool_stocks": self.attention_pool_stocks,
            "out_of_pool_stocks": self.out_of_pool_stocks,
            "evidence": [e.to_dict() for e in self.evidence],
            "theme_score": round(self.theme_score, 2),
            "theme_level": self.theme_level.value,
            "theme_status": self.theme_status.value,
            "is_new_theme": self.is_new_theme,
            "is_one_day_noise_candidate": self.is_one_day_noise_candidate,
            "warnings": self.warnings,
            "risks": self.risks,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ThemeCandidate":
        return cls(
            theme_name=d.get("theme_name", ""),
            theme_aliases=d.get("theme_aliases", []),
            related_sectors=d.get("related_sectors", []),
            core_stocks=d.get("core_stocks", []),
            trend_mid_caps=d.get("trend_mid_caps", []),
            elastic_stocks=d.get("elastic_stocks", []),
            replacement_candidates=d.get("replacement_candidates", []),
            attention_pool_stocks=d.get("attention_pool_stocks", []),
            out_of_pool_stocks=d.get("out_of_pool_stocks", []),
            evidence=[ThemeEvidence.from_dict(e) for e in d.get("evidence", [])],
            theme_score=d.get("theme_score", 0.0),
            theme_level=ThemeLevel(d.get("theme_level", "unknown")),
            theme_status=ThemeStatus(d.get("theme_status", "unknown")),
            is_new_theme=d.get("is_new_theme", False),
            is_one_day_noise_candidate=d.get("is_one_day_noise_candidate", False),
            warnings=d.get("warnings", []),
            risks=d.get("risks", []),
        )


# ============================================================================
# Input / Output
# ============================================================================


@dataclass
class ThemeDetectionInput:
    """Input for Theme Detection."""

    trade_date: str = ""
    scan_time: Optional[datetime] = None
    market_scan_result: Optional[Any] = None     # MarketWideScanResult
    attention_pool_items: List[Any] = field(default_factory=list)  # AttentionPoolEntry list
    manual_theme_hints: List[str] = field(default_factory=list)    # User-provided theme hints
    data_statuses: List[Any] = field(default_factory=list)         # DataStatus objects

    def to_dict(self) -> dict:
        return {
            "trade_date": self.trade_date,
            "scan_time": self.scan_time.isoformat() if self.scan_time else None,
            "market_scan_result": self.market_scan_result.to_dict() if self.market_scan_result and hasattr(self.market_scan_result, "to_dict") else None,
            "attention_pool_items": [a.to_dict() if hasattr(a, "to_dict") else a for a in self.attention_pool_items],
            "manual_theme_hints": self.manual_theme_hints,
            "data_statuses": [s.to_dict() if hasattr(s, "to_dict") else s for s in self.data_statuses],
        }


@dataclass
class ThemeDetectionResult:
    """Result of Theme Detection."""

    trade_date: str = ""
    scan_time: Optional[datetime] = None
    theme_candidates: List[ThemeCandidate] = field(default_factory=list)
    strongest_themes: List[str] = field(default_factory=list)      # S/A level theme names
    watch_themes: List[str] = field(default_factory=list)          # B level theme names
    weak_or_noise_themes: List[str] = field(default_factory=list)  # C level theme names
    data_freshness_result: Optional[Any] = None                    # ReportFreshnessResult
    warnings: List[str] = field(default_factory=list)
    blocking_reasons: List[str] = field(default_factory=list)
    can_continue_to_candidate_selection: bool = True

    def to_dict(self) -> dict:
        return {
            "trade_date": self.trade_date,
            "scan_time": self.scan_time.isoformat() if self.scan_time else None,
            "theme_candidates": [t.to_dict() for t in self.theme_candidates],
            "strongest_themes": self.strongest_themes,
            "watch_themes": self.watch_themes,
            "weak_or_noise_themes": self.weak_or_noise_themes,
            "data_freshness_result": self.data_freshness_result.to_dict() if self.data_freshness_result and hasattr(self.data_freshness_result, "to_dict") else None,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "can_continue_to_candidate_selection": self.can_continue_to_candidate_selection,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ThemeDetectionResult":
        scan_time = None
        if d.get("scan_time"):
            try:
                scan_time = datetime.fromisoformat(d["scan_time"])
            except (ValueError, TypeError):
                pass

        return cls(
            trade_date=d.get("trade_date", ""),
            scan_time=scan_time,
            theme_candidates=[ThemeCandidate.from_dict(t) for t in d.get("theme_candidates", [])],
            strongest_themes=d.get("strongest_themes", []),
            watch_themes=d.get("watch_themes", []),
            weak_or_noise_themes=d.get("weak_or_noise_themes", []),
            warnings=d.get("warnings", []),
            blocking_reasons=d.get("blocking_reasons", []),
            can_continue_to_candidate_selection=d.get("can_continue_to_candidate_selection", True),
        )
