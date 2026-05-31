"""Market-Wide Scan data schemas.

These schemas define the structure for full market scanning in A-stock market.
Market-Wide Scan is used to judge market environment, sentiment, sector strength,
theme candidates, and out-of-pool opportunities.

NOTE: This is Phase 3B - data structure skeleton only.
No real data fetching, no theme detection algorithm, no trading recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# Enums
# ============================================================================


class MarketTemperature(str, Enum):
    """Market temperature classification."""
    STRONG_EXPANSION = "strong_expansion"      # 强势增量市场
    STRUCTURAL_ACTIVE = "structural_active"    # 结构性活跃市场
    ROTATION = "rotation"                      # 存量轮动市场
    WEAK_SHRINKING = "weak_shrinking"          # 缩量弱势市场
    SELLOFF = "selloff"                        # 退潮杀跌市场
    ICE_REPAIR = "ice_repair"                  # 冰点修复市场
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"
    UNKNOWN = "unknown"


class ThemeCandidateStatus(str, Enum):
    """Theme candidate status."""
    STRONG_CANDIDATE = "strong_candidate"      # 强候选主线
    WATCH_CANDIDATE = "watch_candidate"        # 观察候选
    WEAK_CANDIDATE = "weak_candidate"          # 弱候选
    ONE_DAY_NOISE = "one_day_noise"            # 一日游
    UNKNOWN = "unknown"


# ============================================================================
# Snapshot schemas
# ============================================================================


@dataclass
class IndexSnapshot:
    """Snapshot of a market index."""

    index_code: str                            # e.g., "000001.SH", "399001.SZ"
    index_name: str                            # e.g., "上证指数", "深证成指"
    latest_price: float                        # Latest price
    pct_change: float                          # Percentage change (e.g., 1.5 for +1.5%)
    turnover: Optional[float] = None           # Turnover in 亿元
    volume: Optional[float] = None             # Volume
    as_of_time: Optional[datetime] = None      # Data timestamp
    source: str = ""                           # Data source

    def to_dict(self) -> dict:
        return {
            "index_code": self.index_code,
            "index_name": self.index_name,
            "latest_price": self.latest_price,
            "pct_change": self.pct_change,
            "turnover": self.turnover,
            "volume": self.volume,
            "as_of_time": self.as_of_time.isoformat() if self.as_of_time else None,
            "source": self.source,
        }


@dataclass
class MarketBreadthSnapshot:
    """Market breadth data (涨跌家数)."""

    up_count: int = 0                          # 上涨家数
    down_count: int = 0                        # 下跌家数
    flat_count: int = 0                        # 平盘家数
    limit_up_count: int = 0                    # 涨停家数
    limit_down_count: int = 0                  # 跌停家数
    real_limit_up_count: int = 0               # 实际涨停家数（排除ST等）
    real_limit_down_count: int = 0             # 实际跌停家数
    broken_limit_up_count: int = 0             # 炸板家数
    limit_up_open_fail_count: int = 0          # 涨停打开失败家数
    high_board_height: int = 0                 # 最高连板高度
    as_of_time: Optional[datetime] = None
    source: str = ""

    def to_dict(self) -> dict:
        return {
            "up_count": self.up_count,
            "down_count": self.down_count,
            "flat_count": self.flat_count,
            "limit_up_count": self.limit_up_count,
            "limit_down_count": self.limit_down_count,
            "real_limit_up_count": self.real_limit_up_count,
            "real_limit_down_count": self.real_limit_down_count,
            "broken_limit_up_count": self.broken_limit_up_count,
            "limit_up_open_fail_count": self.limit_up_open_fail_count,
            "high_board_height": self.high_board_height,
            "as_of_time": self.as_of_time.isoformat() if self.as_of_time else None,
            "source": self.source,
        }


@dataclass
class TurnoverSnapshot:
    """Market turnover snapshot (成交额)."""

    total_market_turnover: float = 0.0         # 两市总成交额（亿元）
    sh_turnover: Optional[float] = None        # 沪市成交额
    sz_turnover: Optional[float] = None        # 深市成交额
    bj_turnover: Optional[float] = None        # 北交所成交额
    turnover_change_vs_previous_day: Optional[float] = None  # 较前日变化百分比
    as_of_time: Optional[datetime] = None
    source: str = ""

    def to_dict(self) -> dict:
        return {
            "total_market_turnover": self.total_market_turnover,
            "sh_turnover": self.sh_turnover,
            "sz_turnover": self.sz_turnover,
            "bj_turnover": self.bj_turnover,
            "turnover_change_vs_previous_day": self.turnover_change_vs_previous_day,
            "as_of_time": self.as_of_time.isoformat() if self.as_of_time else None,
            "source": self.source,
        }


@dataclass
class SectorSnapshot:
    """Snapshot of a sector/板块."""

    sector_code: str = ""                      # Sector code
    sector_name: str = ""                      # Sector name
    pct_change: float = 0.0                    # Percentage change
    turnover: Optional[float] = None           # Turnover in 亿元
    turnover_rank: Optional[int] = None        # Turnover rank
    limit_up_count: int = 0                    # Limit-up count in sector
    strong_stock_count: int = 0                # Strong stock count
    leading_stocks: List[str] = field(default_factory=list)  # Leading stock tickers
    source: str = ""
    as_of_time: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "sector_code": self.sector_code,
            "sector_name": self.sector_name,
            "pct_change": self.pct_change,
            "turnover": self.turnover,
            "turnover_rank": self.turnover_rank,
            "limit_up_count": self.limit_up_count,
            "strong_stock_count": self.strong_stock_count,
            "leading_stocks": self.leading_stocks,
            "source": self.source,
            "as_of_time": self.as_of_time.isoformat() if self.as_of_time else None,
        }


@dataclass
class StrongStockSnapshot:
    """Snapshot of a strong stock."""

    ticker: str = ""                           # Stock code
    name: str = ""                             # Stock name
    pct_change: float = 0.0                    # Percentage change
    turnover: Optional[float] = None           # Turnover in 万元/亿元
    rank_by_turnover: Optional[int] = None     # Rank by turnover
    rank_by_pct_change: Optional[int] = None   # Rank by pct_change
    is_limit_up: bool = False                  # Is limit up
    is_broken_limit_up: bool = False           # Is broken limit up (炸板)
    board_type: str = ""                       # Board type
    sector_names: List[str] = field(default_factory=list)  # Belonging sectors
    source: str = ""
    as_of_time: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "pct_change": self.pct_change,
            "turnover": self.turnover,
            "rank_by_turnover": self.rank_by_turnover,
            "rank_by_pct_change": self.rank_by_pct_change,
            "is_limit_up": self.is_limit_up,
            "is_broken_limit_up": self.is_broken_limit_up,
            "board_type": self.board_type,
            "sector_names": self.sector_names,
            "source": self.source,
            "as_of_time": self.as_of_time.isoformat() if self.as_of_time else None,
        }


@dataclass
class LimitUpPoolSnapshot:
    """Snapshot of limit-up/down pool."""

    trade_date: str = ""                       # Trade date
    limit_up_stocks: List[str] = field(default_factory=list)       # Limit-up tickers
    limit_down_stocks: List[str] = field(default_factory=list)     # Limit-down tickers
    broken_limit_up_stocks: List[str] = field(default_factory=list)  # Broken limit-up tickers
    high_board_height: int = 0                 # Highest board height
    source: str = ""
    as_of_time: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "trade_date": self.trade_date,
            "limit_up_stocks": self.limit_up_stocks,
            "limit_down_stocks": self.limit_down_stocks,
            "broken_limit_up_stocks": self.broken_limit_up_stocks,
            "high_board_height": self.high_board_height,
            "source": self.source,
            "as_of_time": self.as_of_time.isoformat() if self.as_of_time else None,
        }


# ============================================================================
# Theme and Out-of-Pool signals
# ============================================================================


@dataclass
class ThemeCandidateSignal:
    """Theme candidate signal (主题候选信号).

    NOTE: This is a data structure only. Theme detection algorithm
    will be implemented in a later phase.
    """

    theme_name: str = ""                       # Theme name
    evidence_sectors: List[str] = field(default_factory=list)    # Evidence sectors
    evidence_stocks: List[str] = field(default_factory=list)     # Evidence stocks
    sector_strength_score: float = 0.0         # Sector strength score
    limit_up_support_score: float = 0.0        # Limit-up support score
    turnover_support_score: float = 0.0        # Turnover support score
    attention_pool_overlap_count: int = 0      # Overlap with Attention Pool
    is_new_theme_candidate: bool = False       # Is new theme candidate
    status: ThemeCandidateStatus = ThemeCandidateStatus.UNKNOWN
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "theme_name": self.theme_name,
            "evidence_sectors": self.evidence_sectors,
            "evidence_stocks": self.evidence_stocks,
            "sector_strength_score": self.sector_strength_score,
            "limit_up_support_score": self.limit_up_support_score,
            "turnover_support_score": self.turnover_support_score,
            "attention_pool_overlap_count": self.attention_pool_overlap_count,
            "is_new_theme_candidate": self.is_new_theme_candidate,
            "status": self.status.value,
            "warnings": self.warnings,
        }


@dataclass
class OutOfPoolCandidateSignal:
    """Out-of-pool candidate signal (池外高置信度候选).

    NOTE: This is a data structure only. No real out-of-pool
    recommendations will be generated in this phase.
    """

    ticker: str = ""
    name: str = ""
    theme_name: str = ""
    reason: str = ""
    evidence: List[str] = field(default_factory=list)
    in_attention_pool: bool = False
    requires_replacement: bool = False
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "theme_name": self.theme_name,
            "reason": self.reason,
            "evidence": self.evidence,
            "in_attention_pool": self.in_attention_pool,
            "requires_replacement": self.requires_replacement,
            "warnings": self.warnings,
        }


# ============================================================================
# Input / Output
# ============================================================================


@dataclass
class MarketWideScanInput:
    """Input for Market-Wide Scan."""

    trade_date: str = ""                       # Trade date
    scan_time: Optional[datetime] = None       # Scan time
    indexes: List[IndexSnapshot] = field(default_factory=list)
    market_breadth: Optional[MarketBreadthSnapshot] = None
    turnover: Optional[TurnoverSnapshot] = None
    sectors: List[SectorSnapshot] = field(default_factory=list)
    strong_stocks: List[StrongStockSnapshot] = field(default_factory=list)
    limit_up_pool: Optional[LimitUpPoolSnapshot] = None
    data_statuses: List[Any] = field(default_factory=list)  # DataStatus objects

    def to_dict(self) -> dict:
        return {
            "trade_date": self.trade_date,
            "scan_time": self.scan_time.isoformat() if self.scan_time else None,
            "indexes": [i.to_dict() for i in self.indexes],
            "market_breadth": self.market_breadth.to_dict() if self.market_breadth else None,
            "turnover": self.turnover.to_dict() if self.turnover else None,
            "sectors": [s.to_dict() for s in self.sectors],
            "strong_stocks": [s.to_dict() for s in self.strong_stocks],
            "limit_up_pool": self.limit_up_pool.to_dict() if self.limit_up_pool else None,
            "data_statuses": [s.to_dict() if hasattr(s, "to_dict") else s for s in self.data_statuses],
        }


@dataclass
class MarketWideScanResult:
    """Result of Market-Wide Scan."""

    trade_date: str = ""
    scan_time: Optional[datetime] = None
    market_temperature: MarketTemperature = MarketTemperature.UNKNOWN
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    breadth_summary: str = ""
    turnover_summary: str = ""
    strongest_sectors: List[str] = field(default_factory=list)
    weakest_sectors: List[str] = field(default_factory=list)
    theme_candidates: List[ThemeCandidateSignal] = field(default_factory=list)
    out_of_pool_candidates: List[OutOfPoolCandidateSignal] = field(default_factory=list)
    data_freshness_result: Optional[Any] = None  # ReportFreshnessResult
    warnings: List[str] = field(default_factory=list)
    blocking_reasons: List[str] = field(default_factory=list)
    can_continue_to_theme_detection: bool = True

    def to_dict(self) -> dict:
        return {
            "trade_date": self.trade_date,
            "scan_time": self.scan_time.isoformat() if self.scan_time else None,
            "market_temperature": self.market_temperature.value,
            "risk_level": self.risk_level.value,
            "breadth_summary": self.breadth_summary,
            "turnover_summary": self.turnover_summary,
            "strongest_sectors": self.strongest_sectors,
            "weakest_sectors": self.weakest_sectors,
            "theme_candidates": [t.to_dict() for t in self.theme_candidates],
            "out_of_pool_candidates": [o.to_dict() for o in self.out_of_pool_candidates],
            "data_freshness_result": self.data_freshness_result.to_dict() if self.data_freshness_result else None,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "can_continue_to_theme_detection": self.can_continue_to_theme_detection,
        }
