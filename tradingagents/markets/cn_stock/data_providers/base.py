"""Base provider class for A-stock data providers.

All providers must inherit from BaseCnStockProvider and implement
the required methods. Providers must return ProviderResult and
support conversion to DataStatus.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from .schema import ProviderResult, ProviderStatus

logger = logging.getLogger(__name__)


class BaseCnStockProvider(ABC):
    """Base class for all A-stock data providers.

    Subclasses must implement:
    - provider_name: property returning the provider name
    - supported_datasets: property returning list of supported dataset names
    - fetch(): method to fetch data

    Optional overrides:
    - normalize(): method to normalize raw data (default: identity)
    - validate_result(): method to validate result
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'mootdx', 'tencent')."""
        ...

    @property
    @abstractmethod
    def supported_datasets(self) -> List[str]:
        """Return list of supported dataset names."""
        ...

    @abstractmethod
    def fetch(self, dataset_name: str, **kwargs) -> ProviderResult:
        """Fetch data for the given dataset.

        Args:
            dataset_name: Name of the dataset to fetch
            **kwargs: Additional parameters (e.g., symbol, date range)

        Returns:
            ProviderResult with the fetched data
        """
        ...

    def normalize(self, dataset_name: str, raw_data: Any, **kwargs) -> Any:
        """Normalize raw data to project-standard format.

        Default implementation returns raw_data unchanged.

        Args:
            dataset_name: Name of the dataset
            raw_data: Raw data from fetch()
            **kwargs: Additional parameters

        Returns:
            Normalized data
        """
        return raw_data

    def fetch_and_normalize(self, dataset_name: str, **kwargs) -> ProviderResult:
        """Fetch and normalize data in one call.

        This is the primary method that should be called by consumers.
        It wraps fetch() and normalize() with error handling.
        """
        try:
            result = self.fetch(dataset_name, **kwargs)

            if result.status == ProviderStatus.SUCCESS and result.data is not None:
                try:
                    result.normalized_data = self.normalize(
                        dataset_name, result.data, **kwargs
                    )
                except Exception as e:
                    logger.warning(
                        f"Normalization failed for {self.provider_name}/{dataset_name}: {e}"
                    )
                    result.warnings.append(f"Normalization failed: {e}")

            return result

        except Exception as e:
            logger.error(
                f"Provider {self.provider_name}/{dataset_name} failed: {e}"
            )
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name=dataset_name,
                status=ProviderStatus.FAILED,
                fetched_at=datetime.now(),
                error_message=str(e),
            )

    def validate_result(self, result: ProviderResult) -> ProviderResult:
        """Validate a provider result.

        Can be overridden to add custom validation logic.

        Args:
            result: ProviderResult to validate

        Returns:
            Validated (possibly modified) ProviderResult
        """
        # Basic validation
        if result.status == ProviderStatus.SUCCESS:
            if result.data is None:
                result.status = ProviderStatus.EMPTY
                result.warnings.append("Data is None despite success status")
            if result.fetched_at is None:
                result.fetched_at = datetime.now()

        return result
