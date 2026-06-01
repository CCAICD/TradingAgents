"""Provider orchestration schemas.

These schemas define the unified interface for provider orchestration,
including request definitions, roles, and orchestration results.

Status: Phase 4F - Orchestration / Freshness Aggregation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .schema import ProviderResult, ProviderStatus

logger = logging.getLogger(__name__)


class ProviderRole(str, Enum):
    """Role of a provider in the orchestration pipeline.

    Determines how failures/empty results are handled:
    - primary_market_data: Can block downstream
    - supplementary_data: Only degrades, never blocks
    - disclosure_data: Cannot infer "no major negative" when failed/empty
    - attention_data: Attention evidence, freshness rules apply
    - unknown: Default, conservative handling
    """
    PRIMARY_MARKET_DATA = "primary_market_data"
    SUPPLEMENTARY_DATA = "supplementary_data"
    DISCLOSURE_DATA = "disclosure_data"
    ATTENTION_DATA = "attention_data"
    UNKNOWN = "unknown"


@dataclass
class ProviderRequest:
    """Request for a single provider call.

    Used by orchestrator to dispatch requests to providers.
    """

    provider_name: str = ""                    # Provider name (e.g., "mootdx", "tencent")
    dataset: str = ""                          # Dataset name (e.g., "daily_kline")
    params: Dict[str, Any] = field(default_factory=dict)  # Provider-specific params
    role: ProviderRole = ProviderRole.UNKNOWN  # Role in orchestration
    required: bool = False                     # Whether this request is required
    allow_experimental: bool = False           # Whether to allow experimental providers
    freshness_policy_name: Optional[str] = None  # Freshness policy name
    timeout: Optional[int] = None             # Request timeout

    def to_dict(self) -> dict:
        return {
            "provider_name": self.provider_name,
            "dataset": self.dataset,
            "params": self.params,
            "role": self.role.value,
            "required": self.required,
            "allow_experimental": self.allow_experimental,
            "freshness_policy_name": self.freshness_policy_name,
            "timeout": self.timeout,
        }


@dataclass
class ProviderOrchestrationResult:
    """Result of orchestrating multiple provider requests.

    Contains all provider results, data statuses, and aggregation decisions.
    """

    requests: List[ProviderRequest] = field(default_factory=list)
    provider_results: Dict[str, ProviderResult] = field(default_factory=dict)
    data_statuses: Dict[str, Any] = field(default_factory=dict)  # DataStatus by key
    blocking_issues: List[str] = field(default_factory=list)
    degradation_warnings: List[str] = field(default_factory=list)
    disclosure_unknowns: List[str] = field(default_factory=list)
    freshness_summary: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "requests": [r.to_dict() for r in self.requests],
            "provider_results": {k: v.to_dict() for k, v in self.provider_results.items()},
            "blocking_issues": self.blocking_issues,
            "degradation_warnings": self.degradation_warnings,
            "disclosure_unknowns": self.disclosure_unknowns,
            "freshness_summary": self.freshness_summary,
            "metadata": self.metadata,
        }


@dataclass
class ProviderAggregationDecision:
    """Decision from aggregating provider results.

    Determines whether downstream processing can continue.
    """

    can_continue: bool = True                  # Whether downstream can continue
    blocked_by: List[str] = field(default_factory=list)      # What blocked
    degraded_by: List[str] = field(default_factory=list)      # What degraded
    unknown_by: List[str] = field(default_factory=list)       # What is unknown
    disclosure_unknowns: List[str] = field(default_factory=list)  # Disclosure unknowns
    warnings: List[str] = field(default_factory=list)         # All warnings
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "can_continue": self.can_continue,
            "blocked_by": self.blocked_by,
            "degraded_by": self.degraded_by,
            "unknown_by": self.unknown_by,
            "disclosure_unknowns": self.disclosure_unknowns,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


def run_provider_request(
    request: ProviderRequest,
    registry: Any,
    config: Optional[Dict[str, Any]] = None,
) -> ProviderResult:
    """Run a single provider request.

    Args:
        request: Provider request
        registry: Provider registry
        config: Optional configuration

    Returns:
        ProviderResult from the provider
    """
    from datetime import datetime as dt

    # Check if provider exists
    provider = registry.get(request.provider_name)
    if provider is None:
        return ProviderResult(
            provider_name=request.provider_name,
            dataset_name=request.dataset,
            status=ProviderStatus.FAILED,
            fetched_at=dt.now(),
            error_message=f"Provider not found: {request.provider_name}",
        )

    # Check if provider is experimental and not allowed
    provider_config = registry.get_config(request.provider_name) if hasattr(registry, 'get_config') else None
    if provider_config and provider_config.get("status") == "experimental":
        if not request.allow_experimental:
            return ProviderResult(
                provider_name=request.provider_name,
                dataset_name=request.dataset,
                status=ProviderStatus.SKIPPED,
                fetched_at=dt.now(),
                error_message=f"Experimental provider not allowed: {request.provider_name}",
                warnings=[f"Experimental provider {request.provider_name} requires allow_experimental=True"],
                metadata={"experimental": True, "skipped": True},
            )

    # Check if provider is disabled
    if provider_config and not provider_config.get("enabled", True):
        return ProviderResult(
            provider_name=request.provider_name,
            dataset_name=request.dataset,
            status=ProviderStatus.SKIPPED,
            fetched_at=dt.now(),
            error_message=f"Provider disabled: {request.provider_name}",
            metadata={"disabled": True},
        )

    # Run provider
    try:
        result = provider.fetch_and_normalize(request.dataset, **request.params)
        return result
    except Exception as e:
        logger.error(f"Provider {request.provider_name}/{request.dataset} failed: {e}")
        return ProviderResult(
            provider_name=request.provider_name,
            dataset_name=request.dataset,
            status=ProviderStatus.FAILED,
            fetched_at=dt.now(),
            error_message=f"Provider exception: {e}",
        )


def run_provider_plan(
    requests: List[ProviderRequest],
    registry: Any,
    config: Optional[Dict[str, Any]] = None,
) -> ProviderOrchestrationResult:
    """Run a provider plan (multiple requests).

    Args:
        requests: List of provider requests
        registry: Provider registry
        config: Optional configuration

    Returns:
        ProviderOrchestrationResult with all results
    """
    from .aggregation import build_orchestration_result

    provider_results = {}
    data_statuses = {}

    for request in requests:
        key = f"{request.provider_name}:{request.dataset}"

        # Run request
        result = run_provider_request(request, registry, config)
        provider_results[key] = result

        # Convert to DataStatus
        try:
            from .freshness import provider_result_to_data_status
            data_status = provider_result_to_data_status(result)
            data_statuses[key] = data_status
        except Exception as e:
            logger.warning(f"Failed to convert ProviderResult to DataStatus: {e}")

    # Build orchestration result
    return build_orchestration_result(
        requests=requests,
        provider_results=provider_results,
        data_statuses=data_statuses,
        metadata={
            "plan_executed": True,
            "request_count": len(requests),
        },
    )
