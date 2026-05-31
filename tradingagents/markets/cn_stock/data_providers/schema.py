"""Provider data schemas.

These schemas define the unified interface for all A-stock data providers.
All providers must return ProviderResult which can be converted to DataStatus.

NOTE: Phase 4A - infrastructure only. No real external API calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ProviderStatus(str, Enum):
    """Status of a provider operation."""
    SUCCESS = "success"
    PARTIAL = "partial"
    EMPTY = "empty"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_IMPLEMENTED = "not_implemented"


@dataclass
class ProviderConcurrencyConfig:
    """Concurrency configuration for a provider.

    Controls how many concurrent requests are allowed and
    whether batch requests are preferred over individual requests.

    max_concurrency: Maximum number of concurrent requests.
        - 1: Serial execution (default for external providers)
        - null: No limit (only for local providers)
    batch_preferred: Whether to prefer batch requests over individual requests.
    notes: Human-readable notes about concurrency constraints.
    """
    max_concurrency: Optional[int] = 1
    batch_preferred: bool = False
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "max_concurrency": self.max_concurrency,
            "batch_preferred": self.batch_preferred,
            "notes": self.notes,
        }


@dataclass
class ProviderResult:
    """Unified result from all data providers.

    All providers must return this structure. It can be converted
    to DataStatus for DataFreshnessGuard integration.
    """

    provider_name: str = ""                    # Provider name (e.g., "mootdx", "tencent")
    market: str = "cn_stock"                   # Market identifier
    dataset_name: str = ""                     # Dataset name (e.g., "realtime_quote")
    source: str = ""                           # Data source identifier
    status: ProviderStatus = ProviderStatus.NOT_IMPLEMENTED
    fetched_at: Optional[datetime] = None      # When data was fetched
    as_of_time: Optional[datetime] = None      # Data is current as of this time
    data: Any = None                           # Raw parsed data
    normalized_data: Any = None                # Normalized/standardized data
    raw_payload_path: Optional[str] = None     # Path to saved raw payload
    error_message: Optional[str] = None        # Error details
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "provider_name": self.provider_name,
            "market": self.market,
            "dataset_name": self.dataset_name,
            "source": self.source,
            "status": self.status.value,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "as_of_time": self.as_of_time.isoformat() if self.as_of_time else None,
            "raw_payload_path": self.raw_payload_path,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "metadata": self.metadata,
            # Note: data and normalized_data are not serialized by default
            # as they may contain complex objects
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProviderResult":
        """Create from dictionary (without data/normalized_data)."""
        fetched_at = None
        if d.get("fetched_at"):
            try:
                fetched_at = datetime.fromisoformat(d["fetched_at"])
            except (ValueError, TypeError):
                pass

        as_of_time = None
        if d.get("as_of_time"):
            try:
                as_of_time = datetime.fromisoformat(d["as_of_time"])
            except (ValueError, TypeError):
                pass

        return cls(
            provider_name=d.get("provider_name", ""),
            market=d.get("market", "cn_stock"),
            dataset_name=d.get("dataset_name", ""),
            source=d.get("source", ""),
            status=ProviderStatus(d.get("status", "not_implemented")),
            fetched_at=fetched_at,
            as_of_time=as_of_time,
            raw_payload_path=d.get("raw_payload_path"),
            error_message=d.get("error_message"),
            warnings=d.get("warnings", []),
            metadata=d.get("metadata", {}),
        )


@dataclass
class ProviderConfig:
    """Configuration for a provider."""

    name: str = ""
    enabled: bool = False
    provider_type: str = "external"            # local / external
    status: str = "planned"                    # planned / implemented / deprecated
    datasets: List[str] = field(default_factory=list)
    rate_limit: Optional[Dict[str, Any]] = None
    concurrency: Optional[ProviderConcurrencyConfig] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "enabled": self.enabled,
            "type": self.provider_type,
            "status": self.status,
            "datasets": self.datasets,
            "rate_limit": self.rate_limit,
            "metadata": self.metadata,
        }
        if self.concurrency:
            d["concurrency"] = self.concurrency.to_dict()
        return d
