"""Replacement rules v0.1 skeleton.

This module provides lightweight functions for determining when a candidate
requires a replacement and selecting replacement candidates.

NOTE: Phase 3D - skeleton only. No real replacement algorithm.
"""

from __future__ import annotations

from typing import List, Optional

from .schema import (
    CandidateTradabilityFlag,
    ManualConstraints,
    StockCandidate,
)


def requires_replacement(
    candidate: StockCandidate,
    constraints: Optional[ManualConstraints] = None,
) -> tuple:
    """Check if a candidate requires a replacement.

    Args:
        candidate: Stock candidate to check
        constraints: Manual constraints (uses defaults if None)

    Returns:
        Tuple of (requires_replacement: bool, reason: str)
    """
    if constraints is None:
        constraints = ManualConstraints()

    reasons = []

    # Check non-main-board
    if candidate.is_main_board is False:
        if constraints.prefer_main_board:
            reasons.append("非主板")

    # Check limit up
    if candidate.is_limit_up is True:
        if constraints.avoid_limit_up:
            reasons.append("涨停")

    # Check high price
    if candidate.latest_price is not None:
        if candidate.latest_price > constraints.high_price_threshold:
            reasons.append(f"股价 > {constraints.high_price_threshold}")
    elif CandidateTradabilityFlag.MISSING_PRICE_DATA in candidate.tradability_flags:
        reasons.append("价格数据缺失")

    # Check ST/*ST
    if CandidateTradabilityFlag.ST_OR_STAR_ST in candidate.tradability_flags:
        reasons.append("ST/*ST")

    # Check delisting risk
    if CandidateTradabilityFlag.DELISTING_RISK in candidate.tradability_flags:
        reasons.append("退市风险")

    # Check suspended
    if CandidateTradabilityFlag.SUSPENDED in candidate.tradability_flags:
        reasons.append("停牌")

    # Check low liquidity
    if CandidateTradabilityFlag.LOW_LIQUIDITY in candidate.tradability_flags:
        reasons.append("流动性不足")

    # Check missing data
    if CandidateTradabilityFlag.MISSING_ANNOUNCEMENT_DATA in candidate.tradability_flags:
        reasons.append("公告数据缺失")

    if reasons:
        return True, "、".join(reasons)

    return False, ""


def select_replacement_candidate(
    original: StockCandidate,
    same_theme_candidates: List[StockCandidate],
    constraints: Optional[ManualConstraints] = None,
) -> Optional[StockCandidate]:
    """Select a replacement candidate from the same theme.

    Priority:
    1. Same theme
    2. Main board
    3. Not limit up
    4. Price <= high_price_threshold
    5. Risk not blocked
    6. Higher attention score
    7. No missing data flags

    Args:
        original: Original candidate that needs replacement
        same_theme_candidates: Candidates from the same theme
        constraints: Manual constraints

    Returns:
        Best replacement candidate, or None if no suitable replacement found
    """
    if constraints is None:
        constraints = ManualConstraints()

    # Filter out the original candidate
    candidates = [c for c in same_theme_candidates if c.ticker != original.ticker]

    if not candidates:
        return None

    # Score each candidate for replacement suitability
    scored = []
    for c in candidates:
        score = 0.0

        # Main board bonus
        if c.is_main_board is True:
            score += 100
        elif c.is_main_board is False:
            score -= 50

        # Not limit up bonus
        if c.is_limit_up is False:
            score += 50
        elif c.is_limit_up is True:
            score -= 100

        # Price check
        if c.latest_price is not None:
            if c.latest_price <= constraints.high_price_threshold:
                score += 30
            else:
                score -= 80

        # Risk level
        from .schema import CandidateRiskLevel
        if c.risk_level == CandidateRiskLevel.LOW:
            score += 20
        elif c.risk_level == CandidateRiskLevel.MEDIUM:
            score += 10
        elif c.risk_level == CandidateRiskLevel.HIGH:
            score -= 30
        elif c.risk_level == CandidateRiskLevel.BLOCKED:
            score -= 200

        # Attention score bonus
        if c.attention_score_20d is not None:
            score += c.attention_score_20d * 0.1

        # Data completeness bonus
        if CandidateTradabilityFlag.MISSING_PRICE_DATA not in c.tradability_flags:
            score += 10
        if CandidateTradabilityFlag.MISSING_ANNOUNCEMENT_DATA not in c.tradability_flags:
            score += 10

        scored.append((c, score))

    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    # Return best candidate if score is positive
    if scored and scored[0][1] > 0:
        return scored[0][0]

    return None
