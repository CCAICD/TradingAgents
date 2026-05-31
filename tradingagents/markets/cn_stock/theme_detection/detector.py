"""Theme Detection result builder.

This module provides a skeleton function for building Theme Detection results.
It does NOT implement real theme detection algorithm or trading recommendations.

NOTE: Phase 3C - skeleton only. No real theme detection, no trading recommendations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from .schema import (
    ThemeCandidate,
    ThemeDetectionInput,
    ThemeDetectionResult,
    ThemeLevel,
    ThemeStatus,
)


def build_theme_detection_result(
    detection_input: ThemeDetectionInput,
    now: Optional[datetime] = None,
) -> ThemeDetectionResult:
    """Build Theme Detection result from input.

    This is a skeleton function that:
    1. Checks if Market-Wide Scan allows continuation
    2. Generates basic warnings
    3. Returns empty or pass-through theme candidates
    4. Does NOT implement real theme detection algorithm
    5. Does NOT generate trading recommendations

    Args:
        detection_input: Theme Detection input data
        now: Current time (for testing)

    Returns:
        ThemeDetectionResult with basic structure
    """
    if now is None:
        now = datetime.now()

    result = ThemeDetectionResult(
        trade_date=detection_input.trade_date,
        scan_time=detection_input.scan_time or now,
    )

    # Check if Market-Wide Scan allows continuation
    if detection_input.market_scan_result is not None:
        if hasattr(detection_input.market_scan_result, "can_continue_to_theme_detection"):
            if not detection_input.market_scan_result.can_continue_to_theme_detection:
                result.can_continue_to_candidate_selection = False
                result.blocking_reasons.append(
                    "Market-Wide Scan freshness check failed, cannot proceed to theme detection"
                )
                if hasattr(detection_input.market_scan_result, "blocking_reasons"):
                    result.blocking_reasons.extend(
                        detection_input.market_scan_result.blocking_reasons
                    )
                return result

    # Check for theme candidates from input
    # In this skeleton, we pass through any candidates from the input
    if hasattr(detection_input, "theme_candidates") and detection_input.theme_candidates:
        result.theme_candidates = detection_input.theme_candidates
    elif hasattr(detection_input, "market_scan_result") and detection_input.market_scan_result:
        # If market_scan_result has theme_candidates, pass them through
        if hasattr(detection_input.market_scan_result, "theme_candidates"):
            result.theme_candidates = detection_input.market_scan_result.theme_candidates

    # Categorize themes by level
    for candidate in result.theme_candidates:
        if candidate.theme_level == ThemeLevel.S or candidate.theme_level == ThemeLevel.A:
            result.strongest_themes.append(candidate.theme_name)
        elif candidate.theme_level == ThemeLevel.B:
            result.watch_themes.append(candidate.theme_name)
        elif candidate.theme_level == ThemeLevel.C:
            result.weak_or_noise_themes.append(candidate.theme_name)

    # Add warnings
    if not result.theme_candidates:
        result.warnings.append("No theme candidates available (skeleton mode)")

    if detection_input.manual_theme_hints:
        result.warnings.append(
            f"Manual theme hints provided: {', '.join(detection_input.manual_theme_hints)}. "
            "These will be used in future versions for guided detection."
        )

    return result
