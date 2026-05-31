# tradingagents/markets/cn_stock/candidate_selection/__init__.py

from .schema import (
    CandidateSourceType,
    CandidateTradabilityFlag,
    CandidateRiskLevel,
    CandidateActionLabel,
    StockCandidate,
    ReplacementCandidate,
    OutOfPoolHighConvictionCandidate,
    CandidateSelectionInput,
    CandidateSelectionResult,
)
from .replacement import requires_replacement, select_replacement_candidate
from .scoring import calculate_candidate_score, CandidateScoreBreakdown
from .selector import build_candidate_selection_result
from .io import load_candidate_selection_input, save_candidate_selection_result

__all__ = [
    "CandidateSourceType",
    "CandidateTradabilityFlag",
    "CandidateRiskLevel",
    "CandidateActionLabel",
    "StockCandidate",
    "ReplacementCandidate",
    "OutOfPoolHighConvictionCandidate",
    "CandidateSelectionInput",
    "CandidateSelectionResult",
    "requires_replacement",
    "select_replacement_candidate",
    "calculate_candidate_score",
    "CandidateScoreBreakdown",
    "build_candidate_selection_result",
    "load_candidate_selection_input",
    "save_candidate_selection_result",
]
