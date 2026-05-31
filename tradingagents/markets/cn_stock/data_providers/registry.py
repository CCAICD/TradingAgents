"""Provider registry for A-stock data providers.

This module provides a registry for managing data providers,
including registration, lookup, and status tracking.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .base import BaseCnStockProvider
from .schema import ProviderConfig, ProviderResult, ProviderStatus

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry for A-stock data providers.

    Usage:
        registry = ProviderRegistry()

        # Register a provider
        registry.register(MyProvider())

        # Get a provider
        provider = registry.get("my_provider")

        # Find providers for a dataset
        providers = registry.find_by_dataset("realtime_quote")
    """

    def __init__(self):
        self._providers: Dict[str, BaseCnStockProvider] = {}
        self._planned: Dict[str, ProviderConfig] = {}

    def register(self, provider: BaseCnStockProvider) -> None:
        """Register a provider.

        Args:
            provider: Provider instance to register

        Raises:
            ValueError: If provider is already registered
        """
        name = provider.provider_name
        if name in self._providers:
            raise ValueError(f"Provider '{name}' is already registered")
        self._providers[name] = provider
        logger.info(f"Registered provider: {name}")

    def register_planned(self, config: ProviderConfig) -> None:
        """Register a planned (not yet implemented) provider.

        Args:
            config: Provider configuration
        """
        self._planned[config.name] = config
        logger.info(f"Registered planned provider: {config.name}")

    def get(self, name: str) -> Optional[BaseCnStockProvider]:
        """Get a registered provider by name.

        Args:
            name: Provider name

        Returns:
            Provider instance, or None if not found
        """
        return self._providers.get(name)

    def get_config(self, name: str) -> Optional[ProviderConfig]:
        """Get provider configuration (registered or planned).

        Args:
            name: Provider name

        Returns:
            ProviderConfig, or None if not found
        """
        # Check registered providers
        if name in self._providers:
            provider = self._providers[name]
            return ProviderConfig(
                name=name,
                enabled=True,
                provider_type="external",
                status="implemented",
                datasets=provider.supported_datasets,
            )

        # Check planned providers
        return self._planned.get(name)

    def find_by_dataset(self, dataset_name: str) -> List[BaseCnStockProvider]:
        """Find all registered providers that support a dataset.

        Args:
            dataset_name: Name of the dataset

        Returns:
            List of providers supporting the dataset
        """
        result = []
        for provider in self._providers.values():
            if dataset_name in provider.supported_datasets:
                result.append(provider)
        return result

    def list_registered(self) -> List[str]:
        """List all registered provider names."""
        return list(self._providers.keys())

    def list_planned(self) -> List[str]:
        """List all planned provider names."""
        return list(self._planned.keys())

    def list_all(self) -> Dict[str, str]:
        """List all providers with their status.

        Returns:
            Dictionary of provider_name -> status
        """
        result = {}
        for name in self._providers:
            result[name] = "implemented"
        for name in self._planned:
            if name not in result:
                result[name] = "planned"
        return result

    def is_registered(self, name: str) -> bool:
        """Check if a provider is registered."""
        return name in self._providers

    def is_planned(self, name: str) -> bool:
        """Check if a provider is planned."""
        return name in self._planned


# Global registry instance
_global_registry: Optional[ProviderRegistry] = None


def get_registry() -> ProviderRegistry:
    """Get the global provider registry.

    Returns:
        Global ProviderRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ProviderRegistry()
    return _global_registry
