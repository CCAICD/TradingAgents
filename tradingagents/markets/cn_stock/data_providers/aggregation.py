"""Provider aggregation module.

This module provides functions for aggregating provider results,
converting to DataStatus, and making aggregation decisions.

Status: Phase 4F - Orchestration / Freshness Aggregation
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .freshness import provider_result_to_data_status
from .orchestrator import (
    ProviderAggregationDecision,
    ProviderOrchestrationResult,
    ProviderRequest,
    ProviderRole,
)
from .schema import ProviderResult, ProviderStatus

logger = logging.getLogger(__name__)


def _get_request_key(request: ProviderRequest) -> str:
    """Get unique key for a request."""
    return f"{request.provider_name}:{request.dataset}"


def _handle_primary_market_data(
    key: str,
    result: ProviderResult,
    data_status: Any,
    decision: ProviderAggregationDecision,
) -> None:
    """Handle primary market data result.

    Rules:
    - failed/stale/invalid => blocking issue
    - partial => degradation warning
    - success => can continue
    """
    if result.status == ProviderStatus.FAILED:
        decision.can_continue = False
        issue = f"Primary market data failed: {key} - {result.error_message or 'unknown error'}"
        decision.blocked_by.append(issue)
        decision.warnings.append(issue)

    elif result.status == ProviderStatus.EMPTY:
        decision.can_continue = False
        issue = f"Primary market data empty: {key}"
        decision.blocked_by.append(issue)
        decision.warnings.append(issue)

    elif result.status == ProviderStatus.PARTIAL:
        warning = f"Primary market data partial: {key}"
        decision.degraded_by.append(warning)
        decision.warnings.append(warning)

    elif result.status == ProviderStatus.NOT_IMPLEMENTED:
        warning = f"Primary market data not implemented: {key}"
        decision.unknown_by.append(warning)
        decision.warnings.append(warning)


def _handle_supplementary_data(
    key: str,
    result: ProviderResult,
    data_status: Any,
    decision: ProviderAggregationDecision,
) -> None:
    """Handle supplementary data result.

    Rules:
    - failed/empty/stale => degradation warning only, never blocks
    - success => no issue
    """
    if result.status == ProviderStatus.FAILED:
        warning = f"Supplementary data failed: {key} - {result.error_message or 'unknown error'}"
        decision.degraded_by.append(warning)
        decision.warnings.append(warning)

    elif result.status == ProviderStatus.EMPTY:
        warning = f"Supplementary data empty: {key} - missing supplementary data"
        decision.degraded_by.append(warning)
        decision.warnings.append(warning)

    elif result.status == ProviderStatus.PARTIAL:
        warning = f"Supplementary data partial: {key}"
        decision.degraded_by.append(warning)
        decision.warnings.append(warning)

    elif result.status == ProviderStatus.NOT_IMPLEMENTED:
        warning = f"Supplementary data not implemented: {key}"
        decision.degraded_by.append(warning)
        decision.warnings.append(warning)


def _handle_disclosure_data(
    key: str,
    result: ProviderResult,
    data_status: Any,
    decision: ProviderAggregationDecision,
) -> None:
    """Handle disclosure data result.

    Rules:
    - failed/empty/stale => cannot infer "no major negative"
    - success => disclosure data available, but no risk judgment
    """
    if result.status == ProviderStatus.FAILED:
        warning = f"Disclosure data failed: {key} - cannot infer no major negative event"
        decision.disclosure_unknowns.append(warning)
        decision.warnings.append(warning)

    elif result.status == ProviderStatus.EMPTY:
        warning = f"Disclosure data empty: {key} - cannot infer no major negative event"
        decision.disclosure_unknowns.append(warning)
        decision.warnings.append(warning)

    elif result.status == ProviderStatus.PARTIAL:
        warning = f"Disclosure data partial: {key} - disclosure information incomplete"
        decision.disclosure_unknowns.append(warning)
        decision.warnings.append(warning)

    elif result.status == ProviderStatus.NOT_IMPLEMENTED:
        warning = f"Disclosure data not implemented: {key} - cannot assess disclosure risk"
        decision.disclosure_unknowns.append(warning)
        decision.warnings.append(warning)


def _handle_attention_data(
    key: str,
    result: ProviderResult,
    data_status: Any,
    decision: ProviderAggregationDecision,
) -> None:
    """Handle attention data result.

    Rules:
    - failed/empty => attention evidence missing, warning
    - success => attention evidence available
    """
    if result.status == ProviderStatus.FAILED:
        warning = f"Attention data failed: {key}"
        decision.degraded_by.append(warning)
        decision.warnings.append(warning)

    elif result.status == ProviderStatus.EMPTY:
        warning = f"Attention data empty: {key}"
        decision.degraded_by.append(warning)
        decision.warnings.append(warning)


def _build_freshness_summary(
    provider_results: Dict[str, ProviderResult],
) -> Dict[str, int]:
    """Build freshness summary from provider results.

    Returns:
        Dict with counts for each status type
    """
    summary = {
        "total_requests": len(provider_results),
        "success_count": 0,
        "partial_count": 0,
        "empty_count": 0,
        "failed_count": 0,
        "not_implemented_count": 0,
        "unknown_count": 0,
        "blocking_count": 0,
        "degradation_count": 0,
        "disclosure_unknown_count": 0,
    }

    for key, result in provider_results.items():
        if result.status == ProviderStatus.SUCCESS:
            summary["success_count"] += 1
        elif result.status == ProviderStatus.PARTIAL:
            summary["partial_count"] += 1
        elif result.status == ProviderStatus.EMPTY:
            summary["empty_count"] += 1
        elif result.status == ProviderStatus.FAILED:
            summary["failed_count"] += 1
        elif result.status == ProviderStatus.NOT_IMPLEMENTED:
            summary["not_implemented_count"] += 1
        else:
            summary["unknown_count"] += 1

    return summary


def aggregate_provider_results(
    requests: List[ProviderRequest],
    provider_results: Dict[str, ProviderResult],
    data_statuses: Optional[Dict[str, Any]] = None,
) -> ProviderAggregationDecision:
    """Aggregate provider results into an aggregation decision.

    Args:
        requests: List of provider requests
        provider_results: Dict of ProviderResult by key
        data_statuses: Optional dict of DataStatus by key

    Returns:
        ProviderAggregationDecision with can_continue, blocking, degradation, etc.
    """
    decision = ProviderAggregationDecision()

    for request in requests:
        key = _get_request_key(request)
        result = provider_results.get(key)

        if result is None:
            # Provider not found or request not executed
            if request.required:
                decision.can_continue = False
                issue = f"Required provider not found: {key}"
                decision.blocked_by.append(issue)
                decision.warnings.append(issue)
            else:
                warning = f"Optional provider not found: {key}"
                decision.unknown_by.append(warning)
                decision.warnings.append(warning)
            continue

        # Get data status if available
        data_status = data_statuses.get(key) if data_statuses else None

        # Handle based on role
        if request.role == ProviderRole.PRIMARY_MARKET_DATA:
            _handle_primary_market_data(key, result, data_status, decision)
        elif request.role == ProviderRole.SUPPLEMENTARY_DATA:
            _handle_supplementary_data(key, result, data_status, decision)
        elif request.role == ProviderRole.DISCLOSURE_DATA:
            _handle_disclosure_data(key, result, data_status, decision)
        elif request.role == ProviderRole.ATTENTION_DATA:
            _handle_attention_data(key, result, data_status, decision)
        else:
            # Unknown role, conservative handling
            _handle_primary_market_data(key, result, data_status, decision)

    return decision


def build_orchestration_result(
    requests: List[ProviderRequest],
    provider_results: Dict[str, ProviderResult],
    data_statuses: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ProviderOrchestrationResult:
    """Build orchestration result from provider results.

    Args:
        requests: List of provider requests
        provider_results: Dict of ProviderResult by key
        data_statuses: Optional dict of DataStatus by key
        metadata: Optional metadata

    Returns:
        ProviderOrchestrationResult with all results and decisions
    """
    # Aggregate results
    decision = aggregate_provider_results(requests, provider_results, data_statuses)

    # Build freshness summary
    freshness_summary = _build_freshness_summary(provider_results)

    # Build result
    result = ProviderOrchestrationResult(
        requests=requests,
        provider_results=provider_results,
        data_statuses=data_statuses or {},
        blocking_issues=decision.blocked_by,
        degradation_warnings=decision.degraded_by,
        disclosure_unknowns=decision.disclosure_unknowns,
        freshness_summary=freshness_summary,
        metadata={
            **(metadata or {}),
            "can_continue": decision.can_continue,
            "blocked_count": len(decision.blocked_by),
            "degradation_count": len(decision.degraded_by),
            "disclosure_unknown_count": len(decision.disclosure_unknowns),
            "aggregation_warnings": decision.warnings,
        },
    )

    return result
