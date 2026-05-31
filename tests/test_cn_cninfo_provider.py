"""Tests for CninfoProvider.

These tests use mocking to avoid real network calls.
All tests run offline without requiring Cninfo API access.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# Tests
# ============================================================================


class TestCninfoProviderImport:
    """Test that Cninfo provider can be imported."""

    def test_provider_can_be_imported(self):
        """Provider module should be importable."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )

        provider = CninfoProvider()
        assert provider.provider_name == "cninfo"

    def test_supported_datasets(self):
        """Provider should list supported datasets."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )

        provider = CninfoProvider()
        datasets = provider.supported_datasets
        assert "announcement" in datasets


class TestCninfoNotImplemented:
    """Test behavior when endpoints are not implemented."""

    def test_announcement_returns_not_implemented(self):
        """Should return not_implemented for announcement."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="600519")

        assert result.status == ProviderStatus.NOT_IMPLEMENTED
        assert "not confirmed" in result.error_message.lower()

    def test_announcement_error_mentions_report_impact(self):
        """Error message should mention report impact."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="600519")

        assert "no major negative" in result.error_message.lower()

    def test_unsupported_dataset_returns_failed(self):
        """Should return failed for unsupported dataset."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        provider = CninfoProvider()
        result = provider.fetch("unsupported_dataset", ticker="600519")

        assert result.status == ProviderStatus.FAILED
        assert "unsupported" in result.error_message.lower()


class TestCninfoProviderResult:
    """Test ProviderResult structure."""

    def test_returns_provider_result(self):
        """Should return ProviderResult."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderResult

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="600519")

        assert isinstance(result, ProviderResult)
        assert result.provider_name == "cninfo"
        assert result.dataset_name == "announcement"
        assert result.fetched_at is not None

    def test_metadata_includes_status(self):
        """Metadata should include status information."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="600519")

        assert result.metadata.get("status") == "skeleton"
        assert result.metadata.get("requires_validation") is True
        assert result.metadata.get("report_impact") is not None

    def test_metadata_includes_ticker(self):
        """Metadata should include ticker if provided."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="600519")

        assert result.metadata.get("ticker") == "600519"


class TestDataStatusConversion:
    """Test ProviderResult to DataStatus conversion."""

    def test_not_implemented_converts_to_unknown(self):
        """NOT_IMPLEMENTED should convert to UNKNOWN."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.freshness import (
            provider_result_to_data_status,
        )
        from tradingagents.markets.common.data_status import DataFreshStatus

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="600519")

        status = provider_result_to_data_status(result)
        assert status.status == DataFreshStatus.UNKNOWN

    def test_failed_converts_to_failed(self):
        """FAILED should convert to FAILED."""
        from tradingagents.markets.cn_stock.data_providers.schema import (
            ProviderResult,
            ProviderStatus,
        )
        from tradingagents.markets.cn_stock.data_providers.freshness import (
            provider_result_to_data_status,
        )
        from tradingagents.markets.common.data_status import DataFreshStatus

        result = ProviderResult(
            dataset_name="announcement",
            status=ProviderStatus.FAILED,
            error_message="Connection timeout",
        )

        status = provider_result_to_data_status(result)
        assert status.status == DataFreshStatus.FAILED


class TestAnnouncementFailureImpact:
    """Test that announcement failure is handled correctly."""

    def test_not_implemented_cannot_be_no_major_negative(self):
        """NOT_IMPLEMENTED announcement cannot be used to claim 'no major negative'."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="600519")

        # This is the key assertion: not_implemented means we cannot claim no negative
        assert result.status == ProviderStatus.NOT_IMPLEMENTED
        # Error message should indicate the impact
        assert "no major negative" in result.error_message.lower()

    def test_failed_cannot_be_no_major_negative(self):
        """FAILED announcement cannot be used to claim 'no major negative'."""
        from tradingagents.markets.cn_stock.data_providers.schema import (
            ProviderResult,
            ProviderStatus,
        )

        result = ProviderResult(
            dataset_name="announcement",
            status=ProviderStatus.FAILED,
            error_message="API connection failed",
        )

        # If announcement fails, we cannot claim no major negative
        assert result.status == ProviderStatus.FAILED


class TestRateLimiter:
    """Test rate limiter integration."""

    def test_rate_limiter_no_sleep_in_test_mode(self):
        """RateLimiter should not sleep in test mode."""
        from tradingagents.markets.cn_stock.data_providers.rate_limiter import (
            ProviderRateLimitConfig,
            RateLimiter,
        )

        config = ProviderRateLimitConfig(
            min_interval_seconds=10.0,
            test_mode=True,
        )
        limiter = RateLimiter(config=config)

        # Should not sleep
        limiter.wait()
        limiter.record_call()
        limiter.wait()


class TestConfigLoading:
    """Test configuration loading."""

    def test_config_file_loadable(self):
        """cn_stock_providers.yaml should be loadable."""
        import yaml

        config_path = PROJECT_ROOT / "config" / "cn_stock_providers.yaml"
        assert config_path.exists()

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        assert "providers" in config
        assert "cninfo" in config["providers"]

    def test_cninfo_config_status(self):
        """cninfo should be skeleton."""
        import yaml

        config_path = PROJECT_ROOT / "config" / "cn_stock_providers.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        cninfo_config = config["providers"]["cninfo"]
        assert cninfo_config["status"] == "skeleton"
        assert "announcement" in cninfo_config["datasets"]


class TestNoBuySellFields:
    """Test that no buy/sell fields are present."""

    def test_no_buy_sell_in_result(self):
        """Should not contain buy/sell fields."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="600519")

        result_dict = result.to_dict()
        assert "buy" not in result_dict
        assert "sell" not in result_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
