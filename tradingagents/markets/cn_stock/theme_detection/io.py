"""Theme Detection I/O utilities.

This module provides functions for loading and saving Theme Detection data.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .schema import (
    ThemeCandidate,
    ThemeDetectionInput,
    ThemeDetectionResult,
    ThemeEvidence,
    ThemeEvidenceType,
    ThemeLevel,
    ThemeStatus,
)


def _parse_datetime(s: Optional[str]) -> Optional[datetime]:
    """Parse ISO format datetime string."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def load_theme_detection_input(path: Path) -> ThemeDetectionInput:
    """Load Theme Detection input from JSON file.

    Args:
        path: Path to JSON file

    Returns:
        ThemeDetectionInput
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Parse theme candidates if present
    theme_candidates = []
    for d in data.get("theme_candidates", []):
        evidence_list = []
        for e in d.get("evidence", []):
            evidence_list.append(ThemeEvidence(
                evidence_type=ThemeEvidenceType(e.get("evidence_type", "sector_strength")),
                description=e.get("description", ""),
                source=e.get("source", ""),
                related_sectors=e.get("related_sectors", []),
                related_stocks=e.get("related_stocks", []),
                score_contribution=e.get("score_contribution", 0.0),
                confidence=e.get("confidence", 0.0),
                as_of_time=_parse_datetime(e.get("as_of_time")),
                data_status=e.get("data_status", ""),
            ))

        theme_candidates.append(ThemeCandidate(
            theme_name=d.get("theme_name", ""),
            theme_aliases=d.get("theme_aliases", []),
            related_sectors=d.get("related_sectors", []),
            core_stocks=d.get("core_stocks", []),
            trend_mid_caps=d.get("trend_mid_caps", []),
            elastic_stocks=d.get("elastic_stocks", []),
            replacement_candidates=d.get("replacement_candidates", []),
            attention_pool_stocks=d.get("attention_pool_stocks", []),
            out_of_pool_stocks=d.get("out_of_pool_stocks", []),
            evidence=evidence_list,
            theme_score=d.get("theme_score", 0.0),
            theme_level=ThemeLevel(d.get("theme_level", "unknown")),
            theme_status=ThemeStatus(d.get("theme_status", "unknown")),
            is_new_theme=d.get("is_new_theme", False),
            is_one_day_noise_candidate=d.get("is_one_day_noise_candidate", False),
            warnings=d.get("warnings", []),
            risks=d.get("risks", []),
        ))

    return ThemeDetectionInput(
        trade_date=data.get("trade_date", ""),
        scan_time=_parse_datetime(data.get("scan_time")),
        manual_theme_hints=data.get("manual_theme_hints", []),
    )


def save_theme_detection_result(
    result: ThemeDetectionResult,
    output_path: Path,
) -> None:
    """Save Theme Detection result to JSON file.

    Args:
        result: Theme Detection result
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
