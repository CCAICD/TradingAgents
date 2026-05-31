"""Tests for MootdxProvider.

These tests use mocking to avoid real network calls.
All tests run offline without requiring mootdx to be installed.
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
# Mock Data
# ============================================================================

MOCK_DAILY_KLINE_DATA = [
    {
        "open": 1800.0,
        "close": 1810.0,
        "high": 1820.0,
        "low": 1790.0,
        "volume": 100000,
        "amount": 1800000000,
        "datetime": "2026-05-30 00:00:00",
    },
    {
        "open": 1810.0,
        "close": 1825.0,
        "high": 1830.0,
        "low": 1805.0,
        "volume": 120000,
        "amount": 2190000000,
        "datetime": "2026-05-31 00:00:00",
    },
]

MOCK_QUOTE_DATA = [
    {
        "code": "600519",
        "name": "贵州茅台",
        "price": 1825.0,
        "open": 1810.0,
        "high": 1830.0,
        "low": 1805.0,
        "volume": 120000,
        "amount": 2190000000,
        "bid1": 1824.0,
        "bid1_volume": 100,
        "bid2": 1823.0,
        "bid2_volume": 200,
        "bid3": 1822.0,
        "bid3_volume": 300,
        "bid4": 1821.0,
        "bid4_volume": 400,
        "bid5": 1820.0,
        "bid5_volume": 500,
        "ask1": 1826.0,
        "ask1_volume": 100,
        "ask2": 1827.0,
        "ask2_volume": 200,
        "ask3": 1828.0,
        "ask3_volume": 300,
        "ask4": 1829.0,
        "ask4_volume": 400,
        "ask5": 1830.0,
        "ask5_volume": 500,
        "datetime": "2026-05-31 14:30:00",
    }
]

MOCK_QUOTE_WITHOUT_ORDER_BOOK = [
    {
        "code": "600519",
        "name": "贵州茅台",
        "price": 1825.0,
        "open": 1810.0,
        "high": 1830.0,
        "low": 1805.0,
        "volume": 120000,
        "amount": 2190000000,
        "datetime": "2026-05-31 14:30:00",
    }
]


# ============================================================================
# Tests
# ============================================================================


class TestMootdxProviderImport:
    """Test that mootdx provider can be imported without mootdx installed."""

    def test_provider_can_be_imported(self):
        """Provider module should be importable even without mootdx."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()
        assert provider.provider_name == "mootdx"

    def test_supported_datasets(self):
        """Provider should list supported datasets."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()
        datasets = provider.supported_datasets
        assert "daily_kline" in datasets
        assert "minute_kline" in datasets
        assert "index_kline" in datasets
        assert "realtime_quote" in datasets
        assert "order_book" in datasets


class TestMootdxNotInstalled:
    """Test behavior when mootdx is not installed."""

    def test_fetch_returns_failed_when_mootdx_missing(self):
        """Should return failed ProviderResult when mootdx not installed."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()

        with patch.object(provider, "_check_mootdx_available", return_value="mootdx is not installed"):
            result = provider.fetch("daily_kline", symbol="600519")

        assert result.status.value == "failed"
        assert "not installed" in result.error_message.lower()

    def test_fetch_and_normalize_returns_failed_when_mootdx_missing(self):
        """fetch_and_normalize should return failed when mootdx not installed."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()

        with patch.object(provider, "_check_mootdx_available", return_value="mootdx is not installed"):
            result = provider.fetch_and_normalize("daily_kline", symbol="600519")

        assert result.status.value == "failed"
        assert "not installed" in result.error_message.lower()


class TestDailyKline:
    """Test daily_kline dataset."""

    def test_daily_kline_success(self):
        """Should return success with valid data."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()

        # Mock the quotes client
        mock_client = MagicMock()
        mock_client.bars.return_value = MOCK_DAILY_KLINE_DATA

        with patch.object(provider, "_get_quotes_client", return_value=(mock_client, None)):
            result = provider.fetch("daily_kline", symbol="600519", count=10)

        assert result.status.value == "success"
        assert result.provider_name == "mootdx"
        assert result.dataset_name == "daily_kline"
        assert result.data is not None
        assert result.fetched_at is not None

    def test_daily_kline_normalization(self):
        """Should normalize data correctly."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()

        mock_client = MagicMock()
        mock_client.bars.return_value = MOCK_DAILY_KLINE_DATA

        with patch.object(provider, "_get_quotes_client", return_value=(mock_client, None)):
            result = provider.fetch_and_normalize("daily_kline", symbol="600519.SH", count=10)

        assert result.status.value == "success"
        assert result.normalized_data is not None
        assert isinstance(result.normalized_data, list)
        assert len(result.normalized_data) == 2

    def test_daily_kline_missing_symbol(self):
        """Should return failed when symbol is missing."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()
        result = provider.fetch("daily_kline")

        assert result.status.value == "failed"
        assert "symbol is required" in result.error_message.lower()

    def test_daily_kline_empty_result(self):
        """Should return empty when no data."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()

        mock_client = MagicMock()
        mock_client.bars.return_value = None

        with patch.object(provider, "_get_quotes_client", return_value=(mock_client, None)):
            result = provider.fetch("daily_kline", symbol="600519")

        assert result.status.value == "empty"


class TestMinuteKline:
    """Test minute_kline dataset."""

    def test_minute_kline_success(self):
        """Should return success with valid data."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()

        mock_client = MagicMock()
        mock_client.bars.return_value = MOCK_DAILY_KLINE_DATA

        with patch.object(provider, "_get_quotes_client", return_value=(mock_client, None)):
            result = provider.fetch("minute_kline", symbol="600519", frequency="1min", count=10)

        assert result.status.value == "success"
        assert result.dataset_name == "minute_kline"

    def test_minute_kline_missing_symbol(self):
        """Should return failed when symbol is missing."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()
        result = provider.fetch("minute_kline")

        assert result.status.value == "failed"


class TestIndexKline:
    """Test index_kline dataset."""

    def test_index_kline_success(self):
        """Should return success with valid data."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()

        mock_client = MagicMock()
        mock_client.index_bars.return_value = MOCK_DAILY_KLINE_DATA

        with patch.object(provider, "_get_quotes_client", return_value=(mock_client, None)):
            result = provider.fetch("index_kline", symbol="000001", count=10)

        assert result.status.value == "success"
        assert result.dataset_name == "index_kline"

    def test_index_kline_missing_symbol(self):
        """Should return failed when symbol is missing."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()
        result = provider.fetch("index_kline")

        assert result.status.value == "failed"


class TestRealtimeQuote:
    """Test realtime_quote dataset."""

    def test_realtime_quote_success(self):
        """Should return success with valid data."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()

        mock_client = MagicMock()
        mock_client.quotes.return_value = MOCK_QUOTE_DATA

        with patch.object(provider, "_get_quotes_client", return_value=(mock_client, None)):
            result = provider.fetch("realtime_quote", symbols=["600519"])

        assert result.status.value == "success"
        assert result.dataset_name == "realtime_quote"
        assert result.data is not None

    def test_realtime_quote_single_symbol(self):
        """Should accept single symbol string."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()

        mock_client = MagicMock()
        mock_client.quotes.return_value = MOCK_QUOTE_DATA

        with patch.object(provider, "_get_quotes_client", return_value=(mock_client, None)):
            result = provider.fetch("realtime_quote", symbol="600519.SH")

        assert result.status.value == "success"

    def test_realtime_quote_missing_symbols(self):
        """Should return failed when symbols is missing."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()
        result = provider.fetch("realtime_quote")

        assert result.status.value == "failed"


class TestOrderBook:
    """Test order_book dataset."""

    def test_order_book_success_with_bid_ask(self):
        """Should return success when bid/ask fields present."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()

        mock_client = MagicMock()
        mock_client.quotes.return_value = MOCK_QUOTE_DATA

        with patch.object(provider, "_get_quotes_client", return_value=(mock_client, None)):
            result = provider.fetch("order_book", symbols=["600519"])

        assert result.status.value == "success"
        assert result.metadata.get("has_order_book") is True

    def test_order_book_partial_without_bid_ask(self):
        """Should return partial when bid/ask fields missing."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()

        mock_client = MagicMock()
        mock_client.quotes.return_value = MOCK_QUOTE_WITHOUT_ORDER_BOOK

        with patch.object(provider, "_get_quotes_client", return_value=(mock_client, None)):
            result = provider.fetch("order_book", symbols=["600519"])

        assert result.status.value == "partial"
        assert len(result.warnings) > 0
        assert result.metadata.get("has_order_book") is False

    def test_order_book_missing_symbols(self):
        """Should return failed when symbols is missing."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()
        result = provider.fetch("order_book")

        assert result.status.value == "failed"


class TestSymbolNormalization:
    """Test symbol normalization and market inference."""

    def test_normalize_symbol_with_suffix(self):
        """Should remove .SH suffix."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()
        assert provider._normalize_symbol("600519.SH") == "600519"
        assert provider._normalize_symbol("000001.SZ") == "000001"

    def test_normalize_symbol_without_suffix(self):
        """Should return as-is."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()
        assert provider._normalize_symbol("600519") == "600519"

    def test_infer_market_shanghai(self):
        """Should infer Shanghai market."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
            MARKET_SH,
        )

        provider = MootdxProvider()

        market, _ = provider._infer_market_from_symbol("600519")
        assert market == MARKET_SH

        market, _ = provider._infer_market_from_symbol("688001")
        assert market == MARKET_SH

    def test_infer_market_shenzhen(self):
        """Should infer Shenzhen market."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
            MARKET_SZ,
        )

        provider = MootdxProvider()

        market, _ = provider._infer_market_from_symbol("000001")
        assert market == MARKET_SZ

        market, _ = provider._infer_market_from_symbol("300001")
        assert market == MARKET_SZ

    def test_infer_market_from_suffix(self):
        """Should use suffix when available."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
            MARKET_SH,
            MARKET_SZ,
        )

        provider = MootdxProvider()

        market, _ = provider._infer_market_from_symbol("600519.SH")
        assert market == MARKET_SH

        market, _ = provider._infer_market_from_symbol("000001.SZ")
        assert market == MARKET_SZ

    def test_infer_market_beijing_warning(self):
        """Should warn for Beijing Exchange symbols."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
            MARKET_BJ,
        )

        provider = MootdxProvider()

        market, warning = provider._infer_market_from_symbol("830001")
        assert market == MARKET_BJ
        assert warning is not None

    def test_infer_market_unknown_warning(self):
        """Should warn for unknown symbols."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()

        market, warning = provider._infer_market_from_symbol("999999")
        assert market == -1
        assert warning is not None


class TestClientError:
    """Test error handling from mootdx client."""

    def test_client_init_failure(self):
        """Should return failed when client initialization fails."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()

        with patch.object(provider, "_get_quotes_client", return_value=(None, "Connection failed")):
            result = provider.fetch("daily_kline", symbol="600519")

        assert result.status.value == "failed"
        assert "Connection failed" in result.error_message

    def test_bars_exception(self):
        """Should return failed when bars() raises exception."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()

        mock_client = MagicMock()
        mock_client.bars.side_effect = Exception("Server timeout")

        with patch.object(provider, "_get_quotes_client", return_value=(mock_client, None)):
            result = provider.fetch("daily_kline", symbol="600519")

        assert result.status.value == "failed"
        assert "Server timeout" in result.error_message


class TestRawPayload:
    """Test raw payload saving."""

    def test_raw_payload_saved(self, tmp_path):
        """Should save raw payload to temporary directory."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.raw_store import RawPayloadStore

        store = RawPayloadStore(base_dir=tmp_path)
        provider = MootdxProvider(raw_store=store)

        mock_client = MagicMock()
        mock_client.bars.return_value = MOCK_DAILY_KLINE_DATA

        with patch.object(provider, "_get_quotes_client", return_value=(mock_client, None)):
            result = provider.fetch("daily_kline", symbol="600519", count=10)

        assert result.raw_payload_path is not None
        assert Path(result.raw_payload_path).exists()


class TestDataStatusConversion:
    """Test ProviderResult to DataStatus conversion."""

    def test_success_converts_to_fresh(self):
        """SUCCESS should convert to FRESH."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.freshness import (
            provider_result_to_data_status,
        )
        from tradingagents.markets.common.data_status import DataFreshStatus

        provider = MootdxProvider()

        mock_client = MagicMock()
        mock_client.bars.return_value = MOCK_DAILY_KLINE_DATA

        with patch.object(provider, "_get_quotes_client", return_value=(mock_client, None)):
            result = provider.fetch("daily_kline", symbol="600519")

        status = provider_result_to_data_status(result)
        assert status.status == DataFreshStatus.FRESH

    def test_failed_converts_to_failed(self):
        """FAILED should convert to FAILED."""
        from tradingagents.markets.cn_stock.data_providers.freshness import (
            provider_result_to_data_status,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import (
            ProviderResult,
            ProviderStatus,
        )
        from tradingagents.markets.common.data_status import DataFreshStatus

        result = ProviderResult(
            dataset_name="daily_kline",
            status=ProviderStatus.FAILED,
            error_message="Connection timeout",
        )

        status = provider_result_to_data_status(result)
        assert status.status == DataFreshStatus.FAILED


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
        assert "mootdx" in config["providers"]

    def test_mootdx_config_status(self):
        """mootdx should be partial_implemented."""
        import yaml

        config_path = PROJECT_ROOT / "config" / "cn_stock_providers.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        mootdx_config = config["providers"]["mootdx"]
        assert mootdx_config["enabled"] is True
        assert mootdx_config["status"] == "partial_implemented"
        assert "daily_kline" in mootdx_config["datasets"]
        assert "realtime_quote" in mootdx_config["datasets"]


class TestUnsupportedDataset:
    """Test unsupported dataset handling."""

    def test_unsupported_dataset_returns_failed(self):
        """Should return failed for unsupported dataset."""
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )

        provider = MootdxProvider()

        with patch.object(provider, "_check_mootdx_available", return_value=None):
            result = provider.fetch("unsupported_dataset", symbol="600519")

        assert result.status.value == "failed"
        assert "unsupported" in result.error_message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
