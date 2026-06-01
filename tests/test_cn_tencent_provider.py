"""Tests for TencentProvider.

These tests use mocking to avoid real network calls.
All tests run offline without requiring Tencent Finance API access.
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

# Mock Tencent response for 600519 (贵州茅台)
MOCK_TENCENT_RESPONSE_600519 = (
    'v_sh600519="1~贵州茅台~600519~1314.93~1326.00~1327.00~9692~5088~4603~'
    '1314.43~2~1314.21~4~1314.20~1~1314.19~1~1314.18~3~'
    '1314.93~4~1314.94~1~1314.95~2~1314.97~5~1315.00~3~~'
    '20260601094441~-11.07~-0.83~1327.00~1303.19~1314.93/9692/1274540564~'
    '9692~127454~0.08~19.87~~1327.00~1303.19~1.80~16437.70~16437.70~6.14~'
    '1458.60~1193.40~2.61~-4~1315.00~15.08~19.97~~~0.34~127454.0564~0.0000~'
    '0~ ~GP-A~-4.52~2.26~3.93~30.53~26.78~1568.00~1250.10~-0.61~-6.15~-7.80~'
    '1250081601~1250081601~-15.38~-7.66~1250081601~~~-10.58~-0.22~~CNY~0~'
    '___D__F__N~1314.00~13~"'
)

# Mock Tencent response for 000001 (平安银行)
MOCK_TENCENT_RESPONSE_000001 = (
    'v_sz000001="51~平安银行~000001~10.88~10.93~10.90~207121~100846~106251~'
    '10.87~1027~10.86~3071~10.85~8292~10.84~5028~10.83~15241~'
    '10.88~3183~10.89~2676~10.90~3004~10.91~1222~10.92~1231~~'
    '20260601094448~-0.05~-0.46~10.91~10.81~10.88/207121/224774734~'
    '207121~22477~0.11~4.90~~10.91~10.81~0.91~2111.33~2111.36~0.45~'
    '12.02~9.84~3.57~21343~10.85~3.63~4.95~~~0.41~22477.4734~0.0000~'
    '0~ ~GP-A~-4.65~1.87~5.50~7.91~0.71~13.09~10.43~0.18~-5.56~0.00~'
    '19405600653~19405918198~48.53~-7.98~19405600653~~~-0.75~0.18~~CNY~0~~10.'
)

MOCK_TENCENT_EMPTY_RESPONSE = 'v_sh000000=""'

MOCK_TENCENT_INVALID_RESPONSE = "invalid response format"


# ============================================================================
# Tests
# ============================================================================


class TestTencentProviderImport:
    """Test that Tencent provider can be imported."""

    def test_provider_can_be_imported(self):
        """Provider module should be importable."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )

        provider = TencentProvider()
        assert provider.provider_name == "tencent"

    def test_supported_datasets(self):
        """Provider should list supported datasets."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )

        provider = TencentProvider()
        datasets = provider.supported_datasets
        assert "valuation" in datasets
        assert "market_cap" in datasets
        assert "turnover_rate" in datasets
        assert "limit_price" in datasets


class TestTencentUnsupportedDataset:
    """Test unsupported dataset handling."""

    def test_unsupported_dataset_returns_not_implemented(self):
        """Should return not_implemented for unsupported dataset."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        provider = TencentProvider()
        result = provider.fetch("unsupported_dataset", ticker="600519.SH")

        assert result.status == ProviderStatus.NOT_IMPLEMENTED


class TestTencentMissingTicker:
    """Test missing ticker handling."""

    def test_missing_ticker_returns_failed(self):
        """Should return failed when ticker is missing."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        provider = TencentProvider()
        result = provider.fetch("valuation")

        assert result.status == ProviderStatus.FAILED
        assert "ticker is required" in result.error_message.lower()


class TestTencentSymbolConversion:
    """Test symbol conversion."""

    def test_convert_shanghai_with_suffix(self):
        """Should convert 600519.SH to sh600519."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            _convert_to_tencent_symbol,
        )

        symbol, warning = _convert_to_tencent_symbol("600519.SH")
        assert symbol == "sh600519"
        assert warning is None

    def test_convert_shenzhen_with_suffix(self):
        """Should convert 000001.SZ to sz000001."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            _convert_to_tencent_symbol,
        )

        symbol, warning = _convert_to_tencent_symbol("000001.SZ")
        assert symbol == "sz000001"
        assert warning is None

    def test_convert_shanghai_without_suffix(self):
        """Should infer sh prefix for 600xxx."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            _convert_to_tencent_symbol,
        )

        symbol, warning = _convert_to_tencent_symbol("600519")
        assert symbol == "sh600519"
        assert warning is None

    def test_convert_shenzhen_without_suffix(self):
        """Should infer sz prefix for 000xxx."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            _convert_to_tencent_symbol,
        )

        symbol, warning = _convert_to_tencent_symbol("000001")
        assert symbol == "sz000001"
        assert warning is None

    def test_convert_beijing_warning(self):
        """Should warn for Beijing exchange symbols."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            _convert_to_tencent_symbol,
        )

        symbol, warning = _convert_to_tencent_symbol("830001")
        assert symbol == "bj830001"
        assert warning is not None
        assert "beijing" in warning.lower()


class TestTencentValuation:
    """Test valuation dataset."""

    @patch("requests.get")
    def test_success_valuation(self, mock_get):
        """Should return success with valuation data."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = MOCK_TENCENT_RESPONSE_600519.encode("gbk")
        mock_response.headers = {"Content-Type": "text/html; charset=GBK"}
        mock_response.text = MOCK_TENCENT_RESPONSE_600519
        mock_get.return_value = mock_response

        provider = TencentProvider()
        result = provider.fetch("valuation", ticker="600519.SH")

        assert result.status == ProviderStatus.SUCCESS
        assert result.normalized_data is not None
        assert result.normalized_data["pe_ratio"] == 19.87
        assert result.normalized_data["pb_ratio"] == 6.14

    @patch("requests.get")
    def test_valuation_metadata(self, mock_get):
        """Should have experimental and supplementary metadata."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = MOCK_TENCENT_RESPONSE_600519.encode("gbk")
        mock_response.headers = {"Content-Type": "text/html; charset=GBK"}
        mock_response.text = MOCK_TENCENT_RESPONSE_600519
        mock_get.return_value = mock_response

        provider = TencentProvider()
        result = provider.fetch("valuation", ticker="600519.SH")

        assert result.metadata.get("experimental") is True
        assert result.metadata.get("supplementary_source") is True


class TestTencentMarketCap:
    """Test market_cap dataset."""

    @patch("requests.get")
    def test_success_market_cap(self, mock_get):
        """Should return success with market cap data."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = MOCK_TENCENT_RESPONSE_600519.encode("gbk")
        mock_response.headers = {"Content-Type": "text/html; charset=GBK"}
        mock_response.text = MOCK_TENCENT_RESPONSE_600519
        mock_get.return_value = mock_response

        provider = TencentProvider()
        result = provider.fetch("market_cap", ticker="600519.SH")

        assert result.status == ProviderStatus.SUCCESS
        assert result.normalized_data["circulating_market_cap"] == 16437.70
        assert result.normalized_data["total_market_cap"] == 16437.70
        assert result.normalized_data["unit"] == "亿元"
        assert result.normalized_data["unit_unverified"] is True


class TestTencentTurnoverRate:
    """Test turnover_rate dataset."""

    @patch("requests.get")
    def test_success_turnover_rate(self, mock_get):
        """Should return success with turnover rate."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = MOCK_TENCENT_RESPONSE_600519.encode("gbk")
        mock_response.headers = {"Content-Type": "text/html; charset=GBK"}
        mock_response.text = MOCK_TENCENT_RESPONSE_600519
        mock_get.return_value = mock_response

        provider = TencentProvider()
        result = provider.fetch("turnover_rate", ticker="600519.SH")

        assert result.status == ProviderStatus.SUCCESS
        assert result.normalized_data["turnover_rate"] == 0.08


class TestTencentLimitPrice:
    """Test limit_price dataset."""

    @patch("requests.get")
    def test_success_limit_price(self, mock_get):
        """Should return success with limit prices."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = MOCK_TENCENT_RESPONSE_600519.encode("gbk")
        mock_response.headers = {"Content-Type": "text/html; charset=GBK"}
        mock_response.text = MOCK_TENCENT_RESPONSE_600519
        mock_get.return_value = mock_response

        provider = TencentProvider()
        result = provider.fetch("limit_price", ticker="600519.SH")

        assert result.status == ProviderStatus.SUCCESS
        assert result.normalized_data["limit_up_price"] == 1458.60
        assert result.normalized_data["limit_down_price"] == 1193.40


class TestTencentErrorResponse:
    """Test error responses."""

    @patch("requests.get")
    def test_http_500(self, mock_get):
        """Should return failed on HTTP 500."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        provider = TencentProvider()
        result = provider.fetch("valuation", ticker="600519.SH")

        assert result.status == ProviderStatus.FAILED
        assert "500" in result.error_message

    @patch("requests.get")
    def test_timeout(self, mock_get):
        """Should return failed on timeout."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus
        import requests as real_requests

        mock_get.side_effect = real_requests.exceptions.Timeout("timeout")

        provider = TencentProvider()
        result = provider.fetch("valuation", ticker="600519.SH")

        assert result.status == ProviderStatus.FAILED
        assert "timeout" in result.error_message.lower()

    @patch("requests.get")
    def test_connection_error(self, mock_get):
        """Should return failed on connection error."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus
        import requests as real_requests

        mock_get.side_effect = real_requests.exceptions.ConnectionError("connection failed")

        provider = TencentProvider()
        result = provider.fetch("valuation", ticker="600519.SH")

        assert result.status == ProviderStatus.FAILED
        assert "connection" in result.error_message.lower()

    @patch("requests.get")
    def test_empty_response(self, mock_get):
        """Should return empty for empty symbol data."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = MOCK_TENCENT_EMPTY_RESPONSE.encode("gbk")
        mock_response.headers = {"Content-Type": "text/html; charset=GBK"}
        mock_response.text = MOCK_TENCENT_EMPTY_RESPONSE
        mock_get.return_value = mock_response

        provider = TencentProvider()
        result = provider.fetch("valuation", ticker="000000.SH")

        assert result.status == ProviderStatus.EMPTY
        assert "missing supplementary data" in str(result.warnings).lower()

    @patch("requests.get")
    def test_invalid_format(self, mock_get):
        """Should return failed for invalid format."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = MOCK_TENCENT_INVALID_RESPONSE.encode("gbk")
        mock_response.headers = {"Content-Type": "text/html; charset=GBK"}
        mock_response.text = MOCK_TENCENT_INVALID_RESPONSE
        mock_get.return_value = mock_response

        provider = TencentProvider()
        result = provider.fetch("valuation", ticker="600519.SH")

        assert result.status == ProviderStatus.FAILED


class TestTencentNoCookies:
    """Test that no cookies are sent."""

    @patch("requests.get")
    def test_no_cookies_sent(self, mock_get):
        """Should not send cookies."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = MOCK_TENCENT_RESPONSE_600519.encode("gbk")
        mock_response.headers = {"Content-Type": "text/html; charset=GBK"}
        mock_response.text = MOCK_TENCENT_RESPONSE_600519
        mock_get.return_value = mock_response

        provider = TencentProvider()
        provider.fetch("valuation", ticker="600519.SH")

        call_kwargs = mock_get.call_args
        headers = call_kwargs[1].get("headers", {})
        assert "Cookie" not in headers
        assert "cookie" not in headers


class TestTencentRawPayload:
    """Test raw payload saving."""

    @patch("requests.get")
    def test_raw_payload_saved(self, mock_get, tmp_path):
        """Should save raw payload."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.raw_store import RawPayloadStore

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = MOCK_TENCENT_RESPONSE_600519.encode("gbk")
        mock_response.headers = {"Content-Type": "text/html; charset=GBK"}
        mock_response.text = MOCK_TENCENT_RESPONSE_600519
        mock_get.return_value = mock_response

        store = RawPayloadStore(base_dir=tmp_path)
        provider = TencentProvider(raw_store=store)
        result = provider.fetch("valuation", ticker="600519.SH")

        assert result.raw_payload_path is not None
        assert Path(result.raw_payload_path).exists()


class TestTencentNoBuySellFields:
    """Test that no buy/sell fields are present."""

    @patch("requests.get")
    def test_no_buy_sell_in_result(self, mock_get):
        """Should not contain buy/sell/recommendation fields."""
        from tradingagents.markets.cn_stock.data_providers.tencent_provider import (
            TencentProvider,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = MOCK_TENCENT_RESPONSE_600519.encode("gbk")
        mock_response.headers = {"Content-Type": "text/html; charset=GBK"}
        mock_response.text = MOCK_TENCENT_RESPONSE_600519
        mock_get.return_value = mock_response

        provider = TencentProvider()
        result = provider.fetch("valuation", ticker="600519.SH")

        result_dict = result.to_dict()
        assert "buy" not in result_dict
        assert "sell" not in result_dict
        assert "recommendation" not in result_dict
        assert "action" not in result_dict

        if result.normalized_data:
            assert "buy" not in result.normalized_data
            assert "sell" not in result.normalized_data
            assert "recommendation" not in result.normalized_data
            assert "action" not in result.normalized_data
            assert "score" not in result.normalized_data
            assert "target_price" not in result.normalized_data
            assert "conclusion" not in result.normalized_data


class TestTencentDataStatusConversion:
    """Test ProviderResult to DataStatus conversion."""

    def test_success_converts_correctly(self):
        """SUCCESS should convert to usable status."""
        from tradingagents.markets.cn_stock.data_providers.schema import (
            ProviderResult,
            ProviderStatus,
        )
        from tradingagents.markets.cn_stock.data_providers.freshness import (
            provider_result_to_data_status,
        )

        result = ProviderResult(
            dataset_name="valuation",
            status=ProviderStatus.SUCCESS,
            fetched_at=datetime.now(),
        )

        status = provider_result_to_data_status(result)
        assert status.status.value in ["fresh", "unknown"]

    def test_empty_only_degrades_supplementary(self):
        """EMPTY should only degrade supplementary data."""
        from tradingagents.markets.cn_stock.data_providers.schema import (
            ProviderResult,
            ProviderStatus,
        )
        from tradingagents.markets.cn_stock.data_providers.freshness import (
            provider_result_to_data_status,
        )

        result = ProviderResult(
            dataset_name="valuation",
            status=ProviderStatus.EMPTY,
            warnings=["empty tencent result should be treated as missing supplementary data"],
        )

        status = provider_result_to_data_status(result)
        assert status.status.value == "missing"

    def test_failed_only_degrades_supplementary(self):
        """FAILED should only degrade supplementary data."""
        from tradingagents.markets.cn_stock.data_providers.schema import (
            ProviderResult,
            ProviderStatus,
        )
        from tradingagents.markets.cn_stock.data_providers.freshness import (
            provider_result_to_data_status,
        )

        result = ProviderResult(
            dataset_name="valuation",
            status=ProviderStatus.FAILED,
            error_message="Connection failed",
        )

        status = provider_result_to_data_status(result)
        assert status.status.value == "failed"


class TestTencentConfig:
    """Test configuration."""

    def test_config_status_experimental(self):
        """tencent should be experimental in config."""
        import yaml

        config_path = PROJECT_ROOT / "config" / "cn_stock_providers.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        tencent_config = config["providers"]["tencent"]
        assert tencent_config["status"] == "experimental"

    def test_config_max_concurrency(self):
        """tencent should have max_concurrency=1."""
        import yaml

        config_path = PROJECT_ROOT / "config" / "cn_stock_providers.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        tencent_config = config["providers"]["tencent"]
        assert tencent_config["concurrency"]["max_concurrency"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
