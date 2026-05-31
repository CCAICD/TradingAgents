"""Rate limiter for data providers.

This module provides rate limiting for external API calls,
especially for Eastmoney (东财) interfaces which have rate limits.

NOTE: Phase 4A - infrastructure only. No real API calls.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProviderRateLimitConfig:
    """Rate limit configuration for a provider."""

    min_interval_seconds: float = 1.0       # Minimum interval between calls
    jitter_seconds: float = 0.3             # Random jitter added to interval
    max_calls_per_minute: Optional[int] = None  # Max calls per minute
    test_mode: bool = False                 # If True, don't actually sleep


class RateLimiter:
    """Rate limiter for data provider calls.

    Usage:
        limiter = RateLimiter(
            config=ProviderRateLimitConfig(
                min_interval_seconds=1.0,
                jitter_seconds=0.3,
            )
        )

        # Before making API call
        limiter.wait()

        # After making API call
        limiter.record_call()
    """

    def __init__(self, config: Optional[ProviderRateLimitConfig] = None):
        """Initialize the rate limiter.

        Args:
            config: Rate limit configuration. Uses defaults if None.
        """
        self._config = config or ProviderRateLimitConfig()
        self._last_call_time: Optional[datetime] = None
        self._call_count: int = 0
        self._minute_start: Optional[datetime] = None

    def wait(self) -> None:
        """Wait until it's safe to make the next API call.

        In test mode, this is a no-op.
        """
        if self._config.test_mode:
            return

        if self._last_call_time is None:
            return

        # Calculate time since last call
        now = datetime.now()
        elapsed = (now - self._last_call_time).total_seconds()

        # Calculate required wait time
        jitter = random.uniform(0, self._config.jitter_seconds)
        required_wait = self._config.min_interval_seconds + jitter

        # Wait if needed
        if elapsed < required_wait:
            sleep_time = required_wait - elapsed
            logger.debug(f"Rate limiter sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

    def record_call(self) -> None:
        """Record that an API call was made."""
        self._last_call_time = datetime.now()
        self._call_count += 1

        # Track calls per minute
        if self._minute_start is None:
            self._minute_start = datetime.now()

        # Reset minute counter if needed
        elapsed = (datetime.now() - self._minute_start).total_seconds()
        if elapsed >= 60:
            self._call_count = 1
            self._minute_start = datetime.now()

    def can_call(self) -> bool:
        """Check if we can make another call within rate limits.

        Returns:
            True if call is allowed
        """
        if self._config.max_calls_per_minute is None:
            return True

        # Check calls per minute
        if self._minute_start is not None:
            elapsed = (datetime.now() - self._minute_start).total_seconds()
            if elapsed >= 60:
                return True  # Minute window expired
            return self._call_count < self._config.max_calls_per_minute

        return True

    @property
    def call_count(self) -> int:
        """Number of calls made in the current minute window."""
        return self._call_count

    @property
    def config(self) -> ProviderRateLimitConfig:
        """Rate limit configuration."""
        return self._config


# Pre-configured rate limiters for known providers
_PROVIDER_LIMITERS: Dict[str, RateLimiter] = {}


def get_provider_limiter(
    provider_name: str,
    config: Optional[ProviderRateLimitConfig] = None,
) -> RateLimiter:
    """Get or create a rate limiter for a provider.

    Args:
        provider_name: Name of the provider
        config: Optional configuration (used only on first call)

    Returns:
        RateLimiter for the provider
    """
    if provider_name not in _PROVIDER_LIMITERS:
        if config is None:
            # Default configs for known providers
            if provider_name == "eastmoney":
                config = ProviderRateLimitConfig(
                    min_interval_seconds=1.0,
                    jitter_seconds=0.3,
                )
            else:
                config = ProviderRateLimitConfig()
        _PROVIDER_LIMITERS[provider_name] = RateLimiter(config)

    return _PROVIDER_LIMITERS[provider_name]
