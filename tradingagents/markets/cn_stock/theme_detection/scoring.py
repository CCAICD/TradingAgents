"""Theme scoring v0.1 skeleton.

This module provides a lightweight, explainable, configurable scoring
function for theme candidates.

NOTE: This is v0.1 skeleton only. It cannot be used as real trading
evidence. It needs real data validation and reflection system iteration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .schema import ThemeEvidence, ThemeEvidenceType


# Scoring weights (configurable)
SECTOR_STRENGTH_WEIGHT = 30
LIMIT_UP_SUPPORT_WEIGHT = 25
TURNOVER_SUPPORT_WEIGHT = 20
ATTENTION_POOL_OVERLAP_WEIGHT = 15
LEADER_STOCK_STRENGTH_WEIGHT = 10
RISK_PENALTY_WEIGHT = -30


@dataclass
class ScoreBreakdown:
    """Breakdown of theme score calculation."""

    sector_strength_score: float = 0.0
    limit_up_support_score: float = 0.0
    turnover_support_score: float = 0.0
    attention_pool_overlap_score: float = 0.0
    leader_stock_strength_score: float = 0.0
    risk_penalty: float = 0.0
    total_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "sector_strength_score": round(self.sector_strength_score, 2),
            "limit_up_support_score": round(self.limit_up_support_score, 2),
            "turnover_support_score": round(self.turnover_support_score, 2),
            "attention_pool_overlap_score": round(self.attention_pool_overlap_score, 2),
            "leader_stock_strength_score": round(self.leader_stock_strength_score, 2),
            "risk_penalty": round(self.risk_penalty, 2),
            "total_score": round(self.total_score, 2),
        }


def calculate_theme_score(evidence: List[ThemeEvidence]) -> ScoreBreakdown:
    """Calculate theme score from evidence list.

    This is a v0.1 skeleton that:
    1. Groups evidence by type
    2. Calculates weighted scores for each type
    3. Applies risk penalties
    4. Returns explainable breakdown

    Args:
        evidence: List of theme evidence

    Returns:
        ScoreBreakdown with detailed scores
    """
    breakdown = ScoreBreakdown()

    for e in evidence:
        # Normalize confidence to 0-1 range
        confidence = max(0.0, min(1.0, e.confidence))

        if e.evidence_type == ThemeEvidenceType.SECTOR_STRENGTH:
            breakdown.sector_strength_score += e.score_contribution * confidence

        elif e.evidence_type == ThemeEvidenceType.LIMIT_UP_CLUSTER:
            breakdown.limit_up_support_score += e.score_contribution * confidence

        elif e.evidence_type == ThemeEvidenceType.TURNOVER_EXPANSION:
            breakdown.turnover_support_score += e.score_contribution * confidence

        elif e.evidence_type == ThemeEvidenceType.ATTENTION_POOL_OVERLAP:
            breakdown.attention_pool_overlap_score += e.score_contribution * confidence

        elif e.evidence_type == ThemeEvidenceType.LEADER_STOCK_STRENGTH:
            breakdown.leader_stock_strength_score += e.score_contribution * confidence

        elif e.evidence_type == ThemeEvidenceType.RISK_WARNING:
            breakdown.risk_penalty += e.score_contribution * confidence

        # Other evidence types (policy, announcement, out_of_pool) are
        # informational and don't directly contribute to score in v0.1

    # Apply weights
    weighted_sector = breakdown.sector_strength_score * SECTOR_STRENGTH_WEIGHT / 100
    weighted_limit_up = breakdown.limit_up_support_score * LIMIT_UP_SUPPORT_WEIGHT / 100
    weighted_turnover = breakdown.turnover_support_score * TURNOVER_SUPPORT_WEIGHT / 100
    weighted_overlap = breakdown.attention_pool_overlap_score * ATTENTION_POOL_OVERLAP_WEIGHT / 100
    weighted_leader = breakdown.leader_stock_strength_score * LEADER_STOCK_STRENGTH_WEIGHT / 100
    # Risk penalty is negative
    weighted_risk = -(breakdown.risk_penalty * abs(RISK_PENALTY_WEIGHT) / 100)

    # Update breakdown with weighted scores
    breakdown.sector_strength_score = weighted_sector
    breakdown.limit_up_support_score = weighted_limit_up
    breakdown.turnover_support_score = weighted_turnover
    breakdown.attention_pool_overlap_score = weighted_overlap
    breakdown.leader_stock_strength_score = weighted_leader
    breakdown.risk_penalty = weighted_risk

    # Total score
    breakdown.total_score = (
        weighted_sector
        + weighted_limit_up
        + weighted_turnover
        + weighted_overlap
        + weighted_leader
        + weighted_risk  # Risk is negative
    )

    return breakdown
