"""Candidate Selection I/O utilities.

This module provides functions for loading and saving Candidate Selection data.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .schema import (
    CandidateSelectionInput,
    CandidateSelectionResult,
    ManualConstraints,
    StockCandidate,
    CandidateSourceType,
    CandidateTradabilityFlag,
    CandidateRiskLevel,
    CandidateActionLabel,
)


def _parse_datetime(s: Optional[str]) -> Optional[datetime]:
    """Parse ISO format datetime string."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def load_candidate_selection_input(path: Path) -> CandidateSelectionInput:
    """Load Candidate Selection input from JSON file.

    Args:
        path: Path to JSON file

    Returns:
        CandidateSelectionInput
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Parse manual constraints
    constraints = ManualConstraints()
    if data.get("manual_constraints"):
        constraints = ManualConstraints.from_dict(data["manual_constraints"])

    return CandidateSelectionInput(
        trade_date=data.get("trade_date", ""),
        scan_time=_parse_datetime(data.get("scan_time")),
        manual_constraints=constraints,
    )


def save_candidate_selection_result(
    result: CandidateSelectionResult,
    output_path: Path,
) -> None:
    """Save Candidate Selection result to JSON file.

    Args:
        result: Candidate Selection result
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
