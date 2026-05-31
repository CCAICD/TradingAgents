"""Candidate scoring v0.1 skeleton.

This module provides a lightweight, explainable scoring function for candidates.

NOTE: Phase 3D - skeleton only. Cannot be used as real trading evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .schema import CandidateTradabilityFlag, StockCandidate


# Scoring weights
ATTENTION_SCORE_WEIGHT = 0.35
THEME_SCORE_WEIGHT = 0.35
TRADABILITY_WEIGHT = 0.15
RISK_PENALTY_WEIGHT = -0.30
DATA_COMPLETENESS_WEIGHT = 0.15


@dataclass
class CandidateScoreBreakdown:
    """Breakdown of candidate score calculation."""

    attention_component: float = 0.0
    theme_component: float = 0.0
    tradability_component: float = 0.0
    risk_penalty: float = 0.0
    data_completeness_component: float = 0.0
    final_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "attention_component": round(self.attention_component, 2),
            "theme_component": round(self.theme_component, 2),
            "tradability_component": round(self.tradability_component, 2),
            "risk_penalty": round(self.risk_penalty, 2),
            "data_completeness_component": round(self.data_completeness_component, 2),
            "final_score": round(self.final_score, 2),
        }


def calculate_candidate_score(
    candidate: StockCandidate,
) -> CandidateScoreBreakdown:
    """Calculate candidate score from candidate data.

    Args:
        candidate: Stock candidate

    Returns:
        CandidateScoreBreakdown with detailed scores
    """
    breakdown = CandidateScoreBreakdown()

    # Attention component (0-100 normalized)
    if candidate.attention_score_20d is not None:
        # Normalize to 0-100 range (assuming max around 150)
        breakdown.attention_component = min(100.0, candidate.attention_score_20d) * ATTENTION_SCORE_WEIGHT

    # Theme component (0-100 normalized)
    if candidate.theme_score is not None:
        breakdown.theme_component = min(100.0, candidate.theme_score) * THEME_SCORE_WEIGHT

    # Tradability component
    tradability_score = 100.0  # Start with full score
    for flag in candidate.tradability_flags:
        if flag == CandidateTradabilityFlag.MAIN_BOARD:
            pass  # No penalty
        elif flag == CandidateTradabilityFlag.NON_MAIN_BOARD:
            tradability_score -= 30
        elif flag == CandidateTradabilityFlag.LIMIT_UP:
            tradability_score -= 80
        elif flag == CandidateTradabilityFlag.HIGH_PRICE:
            tradability_score -= 50
        elif flag == CandidateTradabilityFlag.ST_OR_STAR_ST:
            tradability_score -= 100
        elif flag == CandidateTradabilityFlag.DELISTING_RISK:
            tradability_score -= 100
        elif flag == CandidateTradabilityFlag.SUSPENDED:
            tradability_score -= 100
        elif flag == CandidateTradabilityFlag.LOW_LIQUIDITY:
            tradability_score -= 40
        elif flag == CandidateTradabilityFlag.MISSING_PRICE_DATA:
            tradability_score -= 60
        elif flag == CandidateTradabilityFlag.MISSING_ANNOUNCEMENT_DATA:
            tradability_score -= 40
        elif flag == CandidateTradabilityFlag.MISSING_STRUCTURE_DATA:
            tradability_score -= 30

    tradability_score = max(0.0, tradability_score)
    breakdown.tradability_component = tradability_score * TRADABILITY_WEIGHT

    # Risk penalty
    from .schema import CandidateRiskLevel
    risk_penalty = 0.0
    if candidate.risk_level == CandidateRiskLevel.HIGH:
        risk_penalty = 80.0
    elif candidate.risk_level == CandidateRiskLevel.BLOCKED:
        risk_penalty = 100.0
    elif candidate.risk_level == CandidateRiskLevel.MEDIUM:
        risk_penalty = 40.0

    breakdown.risk_penalty = -(risk_penalty * abs(RISK_PENALTY_WEIGHT))

    # Data completeness component
    completeness_score = 100.0
    missing_count = sum(1 for f in candidate.tradability_flags if f.value.startswith("missing_"))
    completeness_score -= missing_count * 30
    completeness_score = max(0.0, completeness_score)
    breakdown.data_completeness_component = completeness_score * DATA_COMPLETENESS_WEIGHT

    # Final score
    breakdown.final_score = (
        breakdown.attention_component
        + breakdown.theme_component
        + breakdown.tradability_component
        + breakdown.risk_penalty
        + breakdown.data_completeness_component
    )

    return breakdown
