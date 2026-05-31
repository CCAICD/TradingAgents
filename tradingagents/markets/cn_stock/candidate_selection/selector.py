"""Candidate Selection result builder.

This module provides a skeleton function for building Candidate Selection results.
It does NOT implement real stock selection or trading recommendations.

NOTE: Phase 3D - skeleton only. No real stock selection, no trading recommendations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from .replacement import requires_replacement
from .schema import (
    CandidateActionLabel,
    CandidateRiskLevel,
    CandidateSelectionInput,
    CandidateSelectionResult,
    CandidateSourceType,
    CandidateTradabilityFlag,
    StockCandidate,
)
from .scoring import calculate_candidate_score


def build_candidate_selection_result(
    selection_input: CandidateSelectionInput,
    now: Optional[datetime] = None,
) -> CandidateSelectionResult:
    """Build Candidate Selection result from input.

    This is a skeleton function that:
    1. Checks if Theme Detection allows continuation
    2. Generates basic structure
    3. Checks replacement requirements
    4. Does NOT implement real stock selection
    5. Does NOT generate trading recommendations

    Args:
        selection_input: Candidate Selection input data
        now: Current time (for testing)

    Returns:
        CandidateSelectionResult with basic structure
    """
    if now is None:
        now = datetime.now()

    result = CandidateSelectionResult(
        trade_date=selection_input.trade_date,
        scan_time=selection_input.scan_time or now,
    )

    # Check if Theme Detection allows continuation
    if selection_input.theme_detection_result is not None:
        if hasattr(selection_input.theme_detection_result, "can_continue_to_candidate_selection"):
            if not selection_input.theme_detection_result.can_continue_to_candidate_selection:
                result.can_continue_to_report = False
                result.blocking_reasons.append(
                    "Theme Detection freshness check failed, cannot proceed to candidate selection"
                )
                if hasattr(selection_input.theme_detection_result, "blocking_reasons"):
                    result.blocking_reasons.extend(
                        selection_input.theme_detection_result.blocking_reasons
                    )
                return result

    # Check Data Freshness
    if selection_input.data_freshness_result is not None:
        if hasattr(selection_input.data_freshness_result, "can_generate_strong_conclusion"):
            if not selection_input.data_freshness_result.can_generate_strong_conclusion:
                result.warnings.append(
                    "Data freshness check indicates degraded mode, strong conclusions not allowed"
                )

    # Process candidates from theme detection
    if selection_input.theme_detection_result is not None:
        if hasattr(selection_input.theme_detection_result, "theme_candidates"):
            for theme in selection_input.theme_detection_result.theme_candidates:
                theme_candidates = []
                for stock in theme.core_stocks + theme.trend_mid_caps + theme.elastic_stocks:
                    candidate = StockCandidate(
                        ticker=stock,
                        theme_name=theme.theme_name,
                        source_type=CandidateSourceType.THEME_DETECTION,
                        source_reasons=[f"核心股 - {theme.theme_name}"],
                        theme_score=theme.theme_score,
                    )

                    # Check replacement requirement
                    needs_replacement, reason = requires_replacement(
                        candidate, selection_input.manual_constraints
                    )
                    candidate.requires_replacement = needs_replacement
                    candidate.replacement_reason = reason

                    # Calculate score
                    score_breakdown = calculate_candidate_score(candidate)
                    candidate.candidate_score = score_breakdown.final_score

                    theme_candidates.append(candidate)

                if theme_candidates:
                    result.candidates_by_theme[theme.theme_name] = theme_candidates

    # Add warnings
    if not result.candidates_by_theme:
        result.warnings.append("No candidates available (skeleton mode)")

    return result
