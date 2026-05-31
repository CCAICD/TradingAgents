"""Tests for data provider schema, raw store, registry, and LocalHotlistProvider.

These tests verify:
1. ProviderResult can be created and serialized
2. Base provider exception converts to failed ProviderResult
3. raw_store can save JSON payload
4. raw_store can save text payload
5. raw_store uses project-local or test temp path
6. RateLimiter doesn't sleep in test mode
7. Provider registry can register and get provider
8. Duplicate registration raises error
9. Can find provider by dataset_name
10. Planned provider not treated as implemented
11. LocalHotlistProvider can read attention_pool_latest.json if exists
12. LocalHotlistProvider returns failed/missing on missing file
13. ProviderResult can convert to DataStatus
14. Failed provider result converts to DataStatus failed
15. All existing tests still pass
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.markets.cn_stock.data_providers.schema import (
    ProviderResult,
    ProviderStatus,
    ProviderConfig,
    ProviderConcurrencyConfig,
)
from tradingagents.markets.cn_stock.data_providers.base import BaseCnStockProvider
from tradingagents.markets.cn_stock.data_providers.raw_store import RawPayloadStore
from tradingagents.markets.cn_stock.data_providers.rate_limiter import (
    RateLimiter,
    ProviderRateLimitConfig,
    get_provider_limiter,
)
from tradingagents.markets.cn_stock.data_providers.registry import (
    ProviderRegistry,
    get_registry,
)
from tradingagents.markets.cn_stock.data_providers.freshness import provider_result_to_data_status
from tradingagents.markets.cn_stock.data_providers.local_hotlist_provider import LocalHotlistProvider
from tradingagents.markets.common.data_status import DataFreshStatus


# ============================================================================
# Test Provider for testing base class
# ============================================================================


class TestProvider(BaseCnStockProvider):
    """Test provider for testing base class."""

    @property
    def provider_name(self) -> str:
        return "test_provider"

    @property
    def supported_datasets(self) -> list:
        return ["test_dataset"]

    def fetch(self, dataset_name: str, **kwargs) -> ProviderResult:
        if dataset_name == "test_dataset":
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name=dataset_name,
                status=ProviderStatus.SUCCESS,
                fetched_at=datetime.now(),
                data={"test": "data"},
            )
        return ProviderResult(
            provider_name=self.provider_name,
            dataset_name=dataset_name,
            status=ProviderStatus.FAILED,
            error_message=f"Unknown dataset: {dataset_name}",
        )


class FailingProvider(BaseCnStockProvider):
    """Provider that always fails."""

    @property
    def provider_name(self) -> str:
        return "failing_provider"

    @property
    def supported_datasets(self) -> list:
        return ["failing_dataset"]

    def fetch(self, dataset_name: str, **kwargs) -> ProviderResult:
        raise RuntimeError("Simulated provider failure")


# ============================================================================
# Tests
# ============================================================================


class TestProviderResult:
    """Tests for ProviderResult schema."""

    def test_create_provider_result(self):
        """ProviderResult should be created correctly."""
        result = ProviderResult(
            provider_name="test",
            dataset_name="test_data",
            status=ProviderStatus.SUCCESS,
            fetched_at=datetime.now(),
            data={"key": "value"},
        )

        assert result.provider_name == "test"
        assert result.status == ProviderStatus.SUCCESS

    def test_serialization(self):
        """ProviderResult should serialize to dict."""
        result = ProviderResult(
            provider_name="test",
            dataset_name="test_data",
            status=ProviderStatus.SUCCESS,
            fetched_at=datetime.now(),
            error_message=None,
        )

        d = result.to_dict()
        assert d["provider_name"] == "test"
        assert d["status"] == "success"
        assert d["error_message"] is None

    def test_from_dict(self):
        """ProviderResult should deserialize from dict."""
        now = datetime.now()
        d = {
            "provider_name": "test",
            "dataset_name": "test_data",
            "status": "success",
            "fetched_at": now.isoformat(),
        }

        result = ProviderResult.from_dict(d)
        assert result.provider_name == "test"
        assert result.status == ProviderStatus.SUCCESS

    def test_all_statuses(self):
        """All statuses should be valid."""
        for status in ProviderStatus:
            result = ProviderResult(status=status)
            assert result.status == status


class TestBaseProvider:
    """Tests for BaseCnStockProvider."""

    def test_fetch_and_normalize_success(self):
        """fetch_and_normalize should return normalized result."""
        provider = TestProvider()
        result = provider.fetch_and_normalize("test_dataset")

        assert result.status == ProviderStatus.SUCCESS
        assert result.data == {"test": "data"}
        assert result.normalized_data == {"test": "data"}  # Default: identity

    def test_fetch_and_normalize_failure(self):
        """Exception should convert to failed ProviderResult."""
        provider = FailingProvider()
        result = provider.fetch_and_normalize("failing_dataset")

        assert result.status == ProviderStatus.FAILED
        assert result.error_message is not None
        assert "Simulated" in result.error_message

    def test_unknown_dataset(self):
        """Unknown dataset should return failed."""
        provider = TestProvider()
        result = provider.fetch_and_normalize("unknown_dataset")

        assert result.status == ProviderStatus.FAILED


class TestRawStore:
    """Tests for RawPayloadStore."""

    def test_save_json(self, tmp_path):
        """Should save JSON payload."""
        store = RawPayloadStore(base_dir=tmp_path)
        path = store.save(
            provider_name="test",
            dataset_name="test_data",
            data={"key": "value"},
            symbol="600519",
        )

        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == {"key": "value"}

    def test_save_text(self, tmp_path):
        """Should save text payload."""
        store = RawPayloadStore(base_dir=tmp_path)
        path = store.save(
            provider_name="test",
            dataset_name="test_data",
            data="raw text data",
            file_format="text",
        )

        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == "raw text data"

    def test_default_path(self):
        """Default path should be project-local."""
        store = RawPayloadStore()
        path = store.get_path("test", "test_data")
        assert ".tradingagents" in str(path)
        assert "cn_stock" in str(path)

    def test_exists(self, tmp_path):
        """exists() should check for files."""
        store = RawPayloadStore(base_dir=tmp_path)
        assert not store.exists("test", "test_data")

        store.save(
            provider_name="test",
            dataset_name="test_data",
            data={"key": "value"},
        )
        assert store.exists("test", "test_data")


class TestRateLimiter:
    """Tests for RateLimiter."""

    def test_test_mode_no_sleep(self):
        """Test mode should not sleep."""
        config = ProviderRateLimitConfig(
            min_interval_seconds=10.0,
            test_mode=True,
        )
        limiter = RateLimiter(config=config)

        # Should not sleep
        limiter.wait()
        limiter.record_call()
        limiter.wait()  # Would sleep 10s without test_mode

    def test_record_call(self):
        """record_call should increment count."""
        config = ProviderRateLimitConfig(test_mode=True)
        limiter = RateLimiter(config=config)

        assert limiter.call_count == 0
        limiter.record_call()
        assert limiter.call_count == 1
        limiter.record_call()
        assert limiter.call_count == 2

    def test_can_call(self):
        """can_call should respect max_calls_per_minute."""
        config = ProviderRateLimitConfig(
            max_calls_per_minute=2,
            test_mode=True,
        )
        limiter = RateLimiter(config=config)

        assert limiter.can_call()
        limiter.record_call()
        assert limiter.can_call()
        limiter.record_call()
        assert not limiter.can_call()

    def test_provider_limiter(self):
        """get_provider_limiter should return consistent limiter."""
        limiter1 = get_provider_limiter("test_provider")
        limiter2 = get_provider_limiter("test_provider")
        assert limiter1 is limiter2


class TestProviderRegistry:
    """Tests for ProviderRegistry."""

    def test_register_and_get(self):
        """Should register and get provider."""
        registry = ProviderRegistry()
        provider = TestProvider()
        registry.register(provider)

        assert registry.is_registered("test_provider")
        assert registry.get("test_provider") is provider

    def test_duplicate_registration(self):
        """Duplicate registration should raise error."""
        registry = ProviderRegistry()
        provider = TestProvider()
        registry.register(provider)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(provider)

    def test_find_by_dataset(self):
        """Should find provider by dataset name."""
        registry = ProviderRegistry()
        provider = TestProvider()
        registry.register(provider)

        found = registry.find_by_dataset("test_dataset")
        assert len(found) == 1
        assert found[0] is provider

    def test_find_by_dataset_empty(self):
        """Should return empty for unknown dataset."""
        registry = ProviderRegistry()
        found = registry.find_by_dataset("unknown")
        assert len(found) == 0

    def test_planned_provider(self):
        """Planned provider should not be registered."""
        registry = ProviderRegistry()
        config = ProviderConfig(
            name="planned_provider",
            enabled=False,
            status="planned",
            datasets=["test"],
        )
        registry.register_planned(config)

        assert registry.is_planned("planned_provider")
        assert not registry.is_registered("planned_provider")
        assert registry.get("planned_provider") is None

    def test_list_all(self):
        """list_all should include both registered and planned."""
        registry = ProviderRegistry()
        registry.register(TestProvider())
        registry.register_planned(ProviderConfig(name="planned", status="planned"))

        all_providers = registry.list_all()
        assert "test_provider" in all_providers
        assert "planned" in all_providers
        assert all_providers["test_provider"] == "implemented"
        assert all_providers["planned"] == "planned"


class TestFreshnessConversion:
    """Tests for ProviderResult → DataStatus conversion."""

    def test_success_to_fresh(self):
        """SUCCESS should convert to FRESH."""
        result = ProviderResult(
            dataset_name="test",
            status=ProviderStatus.SUCCESS,
            fetched_at=datetime.now(),
        )

        status = provider_result_to_data_status(result)
        assert status.status == DataFreshStatus.FRESH

    def test_failed_to_failed(self):
        """FAILED should convert to FAILED."""
        result = ProviderResult(
            dataset_name="test",
            status=ProviderStatus.FAILED,
            error_message="Connection timeout",
        )

        status = provider_result_to_data_status(result)
        assert status.status == DataFreshStatus.FAILED
        assert status.error_message == "Connection timeout"

    def test_empty_to_missing(self):
        """EMPTY should convert to MISSING."""
        result = ProviderResult(
            dataset_name="test",
            status=ProviderStatus.EMPTY,
        )

        status = provider_result_to_data_status(result)
        assert status.status == DataFreshStatus.MISSING

    def test_not_implemented_to_unknown(self):
        """NOT_IMPLEMENTED should convert to UNKNOWN."""
        result = ProviderResult(
            dataset_name="test",
            status=ProviderStatus.NOT_IMPLEMENTED,
        )

        status = provider_result_to_data_status(result)
        assert status.status == DataFreshStatus.UNKNOWN

    def test_preserves_metadata(self):
        """Conversion should preserve metadata."""
        result = ProviderResult(
            dataset_name="test",
            status=ProviderStatus.SUCCESS,
            fetched_at=datetime.now(),
            source="test_source",
            raw_payload_path="/tmp/test.json",
            metadata={"key": "value"},
        )

        status = provider_result_to_data_status(result, required=True, max_age_seconds=120)
        assert status.required is True
        assert status.max_age_seconds == 120
        assert status.source == "test_source"
        assert status.raw_payload_path == "/tmp/test.json"


class TestLocalHotlistProvider:
    """Tests for LocalHotlistProvider."""

    def test_provider_name(self):
        """Should have correct provider name."""
        provider = LocalHotlistProvider()
        assert provider.provider_name == "local_hotlist"

    def test_supported_datasets(self):
        """Should support correct datasets."""
        provider = LocalHotlistProvider()
        assert "manual_hotlist" in provider.supported_datasets
        assert "attention_pool" in provider.supported_datasets

    def test_missing_file_returns_empty(self):
        """Missing file should return EMPTY status."""
        provider = LocalHotlistProvider()
        result = provider.fetch("attention_pool", pool_dir="/nonexistent/path")

        assert result.status in (ProviderStatus.EMPTY, ProviderStatus.FAILED)

    def test_unsupported_dataset(self):
        """Unsupported dataset should return FAILED."""
        provider = LocalHotlistProvider()
        result = provider.fetch("unknown_dataset")

        assert result.status == ProviderStatus.FAILED


class TestConcurrencyConfig:
    """Tests for ProviderConcurrencyConfig."""

    def test_concurrency_config_creation(self):
        """ProviderConcurrencyConfig should be created correctly."""
        config = ProviderConcurrencyConfig(
            max_concurrency=1,
            batch_preferred=True,
            notes=["test note"],
        )

        assert config.max_concurrency == 1
        assert config.batch_preferred is True
        assert config.notes == ["test note"]

    def test_concurrency_config_serialization(self):
        """ProviderConcurrencyConfig should serialize to dict."""
        config = ProviderConcurrencyConfig(
            max_concurrency=2,
            batch_preferred=False,
        )

        d = config.to_dict()
        assert d["max_concurrency"] == 2
        assert d["batch_preferred"] is False

    def test_concurrency_config_null_max(self):
        """max_concurrency can be null for local providers."""
        config = ProviderConcurrencyConfig(max_concurrency=None)

        assert config.max_concurrency is None


class TestProviderConfigConcurrency:
    """Tests for ProviderConfig with concurrency."""

    def test_provider_config_with_concurrency(self):
        """ProviderConfig should accept concurrency."""
        concurrency = ProviderConcurrencyConfig(
            max_concurrency=1,
            batch_preferred=True,
        )
        config = ProviderConfig(
            name="test",
            enabled=True,
            concurrency=concurrency,
        )

        assert config.concurrency is not None
        assert config.concurrency.max_concurrency == 1

    def test_provider_config_without_concurrency(self):
        """ProviderConfig should work without concurrency."""
        config = ProviderConfig(name="test")

        assert config.concurrency is None

    def test_provider_config_serialization_with_concurrency(self):
        """ProviderConfig should serialize concurrency."""
        concurrency = ProviderConcurrencyConfig(
            max_concurrency=1,
            batch_preferred=True,
            notes=["test"],
        )
        config = ProviderConfig(
            name="test",
            concurrency=concurrency,
        )

        d = config.to_dict()
        assert "concurrency" in d
        assert d["concurrency"]["max_concurrency"] == 1

    def test_provider_config_serialization_without_concurrency(self):
        """ProviderConfig should not include concurrency when None."""
        config = ProviderConfig(name="test")

        d = config.to_dict()
        assert "concurrency" not in d


class TestConfigConcurrencyLoading:
    """Tests for loading concurrency from config file."""

    def test_config_loads_mootdx_concurrency(self):
        """mootdx should have max_concurrency=1."""
        import yaml

        config_path = PROJECT_ROOT / "config" / "cn_stock_providers.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        mootdx = config["providers"]["mootdx"]
        assert mootdx["concurrency"]["max_concurrency"] == 1
        assert mootdx["concurrency"]["batch_preferred"] is True

    def test_config_loads_tencent_concurrency(self):
        """tencent should have max_concurrency=1."""
        import yaml

        config_path = PROJECT_ROOT / "config" / "cn_stock_providers.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        tencent = config["providers"]["tencent"]
        assert tencent["concurrency"]["max_concurrency"] == 1

    def test_config_loads_cninfo_concurrency(self):
        """cninfo should have max_concurrency=1."""
        import yaml

        config_path = PROJECT_ROOT / "config" / "cn_stock_providers.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        cninfo = config["providers"]["cninfo"]
        assert cninfo["concurrency"]["max_concurrency"] == 1

    def test_config_loads_eastmoney_concurrency(self):
        """eastmoney should have max_concurrency=1."""
        import yaml

        config_path = PROJECT_ROOT / "config" / "cn_stock_providers.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        eastmoney = config["providers"]["eastmoney"]
        assert eastmoney["concurrency"]["max_concurrency"] == 1

    def test_config_loads_local_hotlist_concurrency(self):
        """local_hotlist should have max_concurrency=null."""
        import yaml

        config_path = PROJECT_ROOT / "config" / "cn_stock_providers.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        local = config["providers"]["local_hotlist"]
        assert local["concurrency"]["max_concurrency"] is None

    def test_config_loads_batch_preferred(self):
        """batch_preferred should be loadable."""
        import yaml

        config_path = PROJECT_ROOT / "config" / "cn_stock_providers.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        assert config["providers"]["mootdx"]["concurrency"]["batch_preferred"] is True
        assert config["providers"]["cninfo"]["concurrency"]["batch_preferred"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
