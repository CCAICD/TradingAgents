"""Raw payload storage for data providers.

This module handles saving raw payloads to local storage for
audit trail and debugging purposes.

Default storage path: .tradingagents/raw/cn_stock/<provider_name>/<dataset_name>/
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Default raw payload root
_DEFAULT_RAW_ROOT = Path(__file__).resolve().parents[3] / ".tradingagents" / "raw" / "cn_stock"


class RawPayloadStore:
    """Store for saving raw payloads from data providers.

    Usage:
        store = RawPayloadStore()
        path = store.save(
            provider_name="mootdx",
            dataset_name="realtime_quote",
            data={"symbol": "600519", "price": 1500},
            symbol="600519",
        )
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize the raw payload store.

        Args:
            base_dir: Base directory for raw payloads.
                     Defaults to .tradingagents/raw/cn_stock/
        """
        self._base_dir = base_dir or _DEFAULT_RAW_ROOT

    def save(
        self,
        provider_name: str,
        dataset_name: str,
        data: Any,
        symbol: Optional[str] = None,
        as_of_time: Optional[datetime] = None,
        file_format: str = "json",
    ) -> Path:
        """Save raw payload to local storage.

        Args:
            provider_name: Name of the provider
            dataset_name: Name of the dataset
            data: Raw data to save
            symbol: Optional symbol/market identifier
            as_of_time: Optional data timestamp
            file_format: File format (json or text)

        Returns:
            Path to the saved file
        """
        # Build directory path
        date_str = (as_of_time or datetime.now()).strftime("%Y-%m-%d")
        dir_path = self._base_dir / provider_name / dataset_name / date_str
        dir_path.mkdir(parents=True, exist_ok=True)

        # Build filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        identifier = symbol or "market"
        filename = f"{timestamp}_{identifier}.{file_format}"
        file_path = dir_path / filename

        # Save data
        if file_format == "json":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(str(data))

        return file_path

    def get_path(
        self,
        provider_name: str,
        dataset_name: str,
        date_str: Optional[str] = None,
    ) -> Path:
        """Get the directory path for a provider/dataset/date.

        Args:
            provider_name: Name of the provider
            dataset_name: Name of the dataset
            date_str: Date string (YYYY-MM-DD). Defaults to today.

        Returns:
            Path to the directory
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        return self._base_dir / provider_name / dataset_name / date_str

    def exists(
        self,
        provider_name: str,
        dataset_name: str,
        date_str: Optional[str] = None,
    ) -> bool:
        """Check if raw payloads exist for a provider/dataset/date.

        Args:
            provider_name: Name of the provider
            dataset_name: Name of the dataset
            date_str: Date string (YYYY-MM-DD). Defaults to today.

        Returns:
            True if directory exists and has files
        """
        path = self.get_path(provider_name, dataset_name, date_str)
        return path.exists() and any(path.iterdir())
