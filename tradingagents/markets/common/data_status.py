"""Data status models for Data Freshness Guard.

These models define the structure for tracking data freshness across
all markets and report types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DataFreshStatus(str, Enum):
    """Status of a single dataset."""
    FRESH = "fresh"           # Data is within freshness threshold
    STALE = "stale"           # Data exists but exceeds freshness threshold
    MISSING = "missing"       # Data not found
    FAILED = "failed"         # Fetch/update failed
    PARTIAL = "partial"       # Data is incomplete
    UNKNOWN = "unknown"       # Status cannot be determined


class ReportOverallStatus(str, Enum):
    """Overall status for a report freshness check."""
    OK = "ok"                 # All required data is fresh
    WARNING = "warning"       # Some optional data is stale/missing
    BLOCKED = "blocked"       # Required data is stale/missing/failed
    FAILED = "failed"         # Critical failure


@dataclass
class DataStatus:
    """Status of a single dataset."""

    dataset_name: str                          # e.g., "realtime_quote", "daily_kline"
    market: str                                # e.g., "cn_stock", "us_stock", "crypto"
    source: str                                # e.g., "mootdx", "tencent", "manual_input"
    status: DataFreshStatus = DataFreshStatus.UNKNOWN
    fetched_at: Optional[datetime] = None      # When data was last fetched
    as_of_time: Optional[datetime] = None      # Data is current as of this time
    max_age_seconds: Optional[int] = None      # Freshness threshold (None = no time-based check)
    required: bool = False                     # Whether this dataset is required for the report
    error_message: Optional[str] = None        # Error details if status is FAILED
    raw_payload_path: Optional[str] = None     # Path to raw data file
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "dataset_name": self.dataset_name,
            "market": self.market,
            "source": self.source,
            "status": self.status.value,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "as_of_time": self.as_of_time.isoformat() if self.as_of_time else None,
            "max_age_seconds": self.max_age_seconds,
            "required": self.required,
            "error_message": self.error_message,
            "raw_payload_path": self.raw_payload_path,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DataStatus":
        """Create from dictionary."""
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
            dataset_name=d.get("dataset_name", ""),
            market=d.get("market", ""),
            source=d.get("source", ""),
            status=DataFreshStatus(d.get("status", "unknown")),
            fetched_at=fetched_at,
            as_of_time=as_of_time,
            max_age_seconds=d.get("max_age_seconds"),
            required=d.get("required", False),
            error_message=d.get("error_message"),
            raw_payload_path=d.get("raw_payload_path"),
            metadata=d.get("metadata", {}),
        )


@dataclass
class ReportFreshnessResult:
    """Result of a report freshness check."""

    market: str                                # e.g., "cn_stock"
    report_type: str                           # e.g., "pre_close_report"
    checked_at: datetime = field(default_factory=datetime.now)
    overall_status: ReportOverallStatus = ReportOverallStatus.OK
    can_generate_report: bool = True
    can_generate_strong_conclusion: bool = True
    blocking_reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dataset_statuses: List[DataStatus] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "market": self.market,
            "report_type": self.report_type,
            "checked_at": self.checked_at.isoformat(),
            "overall_status": self.overall_status.value,
            "can_generate_report": self.can_generate_report,
            "can_generate_strong_conclusion": self.can_generate_strong_conclusion,
            "blocking_reasons": self.blocking_reasons,
            "warnings": self.warnings,
            "dataset_statuses": [s.to_dict() for s in self.dataset_statuses],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ReportFreshnessResult":
        """Create from dictionary."""
        checked_at = datetime.now()
        if d.get("checked_at"):
            try:
                checked_at = datetime.fromisoformat(d["checked_at"])
            except (ValueError, TypeError):
                pass

        return cls(
            market=d.get("market", ""),
            report_type=d.get("report_type", ""),
            checked_at=checked_at,
            overall_status=ReportOverallStatus(d.get("overall_status", "ok")),
            can_generate_report=d.get("can_generate_report", True),
            can_generate_strong_conclusion=d.get("can_generate_strong_conclusion", True),
            blocking_reasons=d.get("blocking_reasons", []),
            warnings=d.get("warnings", []),
            dataset_statuses=[DataStatus.from_dict(s) for s in d.get("dataset_statuses", [])],
        )
