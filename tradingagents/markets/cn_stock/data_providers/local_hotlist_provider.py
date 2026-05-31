"""Local hotlist provider.

This provider reads local hotlist and Attention Pool data
without any network calls.

Supported datasets:
- manual_hotlist: Reads from data/manual_hotlists/structured/
- attention_pool: Reads from data/manual_hotlists/attention_pool/

NOTE: Phase 4A - local provider only. No network calls.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from .base import BaseCnStockProvider
from .schema import ProviderResult, ProviderStatus

logger = logging.getLogger(__name__)

# Default data paths
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_STRUCTURED_DIR = _PROJECT_ROOT / "data" / "manual_hotlists" / "structured"
_POOL_DIR = _PROJECT_ROOT / "data" / "manual_hotlists" / "attention_pool"


class LocalHotlistProvider(BaseCnStockProvider):
    """Provider for local hotlist and Attention Pool data.

    This provider reads from local files without network calls.
    """

    @property
    def provider_name(self) -> str:
        return "local_hotlist"

    @property
    def supported_datasets(self) -> List[str]:
        return ["manual_hotlist", "attention_pool"]

    def fetch(self, dataset_name: str, **kwargs) -> ProviderResult:
        """Fetch local hotlist data.

        Args:
            dataset_name: "manual_hotlist" or "attention_pool"
            **kwargs: Optional parameters:
                - date: Date string (YYYY-MM-DD) for manual_hotlist
                - structured_dir: Override structured directory
                - pool_dir: Override pool directory
        """
        now = datetime.now()

        if dataset_name == "manual_hotlist":
            return self._fetch_manual_hotlist(now, **kwargs)
        elif dataset_name == "attention_pool":
            return self._fetch_attention_pool(now, **kwargs)
        else:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name=dataset_name,
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"Unsupported dataset: {dataset_name}",
            )

    def _fetch_manual_hotlist(self, now: datetime, **kwargs) -> ProviderResult:
        """Fetch manual hotlist from structured directory."""
        structured_dir = Path(kwargs.get("structured_dir", _STRUCTURED_DIR))
        date_str = kwargs.get("date")

        if not structured_dir.exists():
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="manual_hotlist",
                source="local_file",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"Structured directory not found: {structured_dir}",
            )

        # Find the latest file
        jsonl_files = sorted(structured_dir.glob("*.jsonl"), reverse=True)
        if not jsonl_files:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="manual_hotlist",
                source="local_file",
                status=ProviderStatus.EMPTY,
                fetched_at=now,
                error_message="No hotlist files found",
            )

        # Use specified date or latest
        if date_str:
            target_file = structured_dir / f"{date_str}.jsonl"
            if not target_file.exists():
                return ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name="manual_hotlist",
                    source="local_file",
                    status=ProviderStatus.EMPTY,
                    fetched_at=now,
                    error_message=f"Hotlist file not found for date: {date_str}",
                )
        else:
            target_file = jsonl_files[0]

        # Read the file
        try:
            records = []
            with open(target_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))

            # Extract date from filename
            file_date = target_file.stem  # e.g., "2026-05-31"
            as_of_time = datetime.strptime(file_date, "%Y-%m-%d")

            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="manual_hotlist",
                source="local_file",
                status=ProviderStatus.SUCCESS,
                fetched_at=now,
                as_of_time=as_of_time,
                data=records,
                metadata={
                    "file_path": str(target_file),
                    "record_count": len(records),
                    "date": file_date,
                },
            )
        except Exception as e:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="manual_hotlist",
                source="local_file",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"Failed to read hotlist file: {e}",
            )

    def _fetch_attention_pool(self, now: datetime, **kwargs) -> ProviderResult:
        """Fetch Attention Pool from latest JSON file."""
        pool_dir = Path(kwargs.get("pool_dir", _POOL_DIR))
        pool_file = pool_dir / "attention_pool_latest.json"

        if not pool_file.exists():
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="attention_pool",
                source="local_file",
                status=ProviderStatus.EMPTY,
                fetched_at=now,
                error_message=f"Attention Pool file not found: {pool_file}",
            )

        try:
            with open(pool_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Try to extract metadata
            metadata = {
                "file_path": str(pool_file),
                "entry_count": len(data) if isinstance(data, list) else 0,
            }

            # Try to find latest trade date from data
            as_of_time = now
            if isinstance(data, list) and data:
                latest_date = None
                for entry in data:
                    if isinstance(entry, dict) and "latest_trade_date" in entry:
                        d = entry["latest_trade_date"]
                        if d and (latest_date is None or d > latest_date):
                            latest_date = d
                if latest_date:
                    try:
                        as_of_time = datetime.strptime(latest_date, "%Y-%m-%d")
                    except ValueError:
                        pass

            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="attention_pool",
                source="local_file",
                status=ProviderStatus.SUCCESS,
                fetched_at=now,
                as_of_time=as_of_time,
                data=data,
                metadata=metadata,
            )
        except Exception as e:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="attention_pool",
                source="local_file",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"Failed to read Attention Pool file: {e}",
            )
