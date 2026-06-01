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
# Mock Data
# ============================================================================

MOCK_CNINFO_RESPONSE = {
    "classifiedAnnouncements": None,
    "totalSecurities": 0,
    "totalAnnouncement": 1980,
    "totalRecordNum": 1980,
    "announcements": [
        {
            "id": None,
            "secCode": "000001",
            "secName": "平安银行",
            "orgId": "gssz0000001",
            "announcementId": "1225327041",
            "announcementTitle": "关于召开2025年度股东大会的通知",
            "announcementTime": 1779465600000,
            "adjunctUrl": "finalpage/2026-05-23/1225327041.PDF",
            "adjunctSize": 186,
            "adjunctType": "PDF",
            "storageTime": None,
            "columnId": "09020202||250101||251302",
            "pageColumn": "SZZB",
            "announcementType": "01010901||010112||011999||012903",
            "associateAnnouncement": None,
            "important": None,
            "batchNum": None,
            "announcementContent": "",
            "orgName": None,
            "tileSecName": "平安银行",
            "shortTitle": "关于召开2025年度股东大会的通知",
            "announcementTypeName": None,
            "secNameList": None,
        },
        {
            "id": None,
            "secCode": "000001",
            "secName": "平安银行",
            "orgId": "gssz0000001",
            "announcementId": "1225327040",
            "announcementTitle": "2025年度股东大会议案公告",
            "announcementTime": 1779465600000,
            "adjunctUrl": "finalpage/2026-05-23/1225327040.PDF",
            "adjunctSize": 145,
            "adjunctType": "PDF",
            "storageTime": None,
            "columnId": "09020202||250101||251302",
            "pageColumn": "SZZB",
            "announcementType": "01010503||010112||011905",
            "associateAnnouncement": None,
            "important": None,
            "batchNum": None,
            "announcementContent": "",
            "orgName": None,
            "tileSecName": "平安银行",
            "shortTitle": "2025年度股东大会议案公告",
            "announcementTypeName": None,
            "secNameList": None,
        },
    ],
    "categoryList": None,
    "hasMore": True,
    "totalpages": 396,
}

MOCK_CNINFO_EMPTY_RESPONSE = {
    "classifiedAnnouncements": None,
    "totalSecurities": 0,
    "totalAnnouncement": 0,
    "totalRecordNum": 0,
    "announcements": None,
    "categoryList": None,
    "hasMore": False,
    "totalpages": 0,
}


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


class TestCninfoUnsupportedDataset:
    """Test unsupported dataset handling."""

    def test_unsupported_dataset_returns_not_implemented(self):
        """Should return not_implemented for unsupported dataset."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        provider = CninfoProvider()
        result = provider.fetch("unsupported_dataset", ticker="000001")

        assert result.status == ProviderStatus.NOT_IMPLEMENTED


class TestCninfoSuccessResponse:
    """Test successful announcement responses."""

    @patch("requests.post")
    def test_success_with_announcements(self, mock_post):
        """Should return success with announcements."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(MOCK_CNINFO_RESPONSE).encode("gbk")
        mock_post.return_value = mock_response

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="000001", org_id="gssz0000001")

        assert result.status == ProviderStatus.SUCCESS
        assert result.provider_name == "cninfo"
        assert result.dataset_name == "announcement"
        assert result.normalized_data is not None
        assert len(result.normalized_data) == 2

    @patch("requests.post")
    def test_normalized_fields(self, mock_post):
        """Should normalize announcement fields correctly."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(MOCK_CNINFO_RESPONSE).encode("gbk")
        mock_post.return_value = mock_response

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="000001", org_id="gssz0000001")

        ann = result.normalized_data[0]
        assert ann["announcement_id"] == "1225327041"
        assert ann["ticker"] == "000001"
        assert ann["org_id"] == "gssz0000001"
        assert ann["source"] == "cninfo"
        assert ann["risk_level_candidate"] == "not_evaluated"
        assert ann["matched_keywords"] == []

    @patch("requests.post")
    def test_pdf_url_construction(self, mock_post):
        """Should construct PDF URL correctly."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(MOCK_CNINFO_RESPONSE).encode("gbk")
        mock_post.return_value = mock_response

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="000001", org_id="gssz0000001")

        ann = result.normalized_data[0]
        assert ann["pdf_url"] is not None
        assert "static.cninfo.com.cn" in ann["pdf_url"]
        assert "1225327041.PDF" in ann["pdf_url"]


class TestCninfoEmptyResponse:
    """Test empty announcement responses."""

    @patch("requests.post")
    def test_empty_announcements(self, mock_post):
        """Should return empty status."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(MOCK_CNINFO_EMPTY_RESPONSE).encode("gbk")
        mock_post.return_value = mock_response

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="000001", org_id="gssz0000001")

        assert result.status == ProviderStatus.EMPTY
        assert "must not be interpreted as no major negative" in str(result.warnings).lower()

    @patch("requests.post")
    def test_empty_warning_message(self, mock_post):
        """Empty result should have warning about no major negative."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(MOCK_CNINFO_EMPTY_RESPONSE).encode("gbk")
        mock_post.return_value = mock_response

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="000001")

        # Check warning message
        warning_text = " ".join(result.warnings).lower()
        assert "no major negative" in warning_text


class TestCninfoErrorResponse:
    """Test error responses."""

    @patch("requests.post")
    def test_http_500(self, mock_post):
        """Should return failed on HTTP 500."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="000001")

        assert result.status == ProviderStatus.FAILED
        assert "500" in result.error_message

    @patch("requests.post")
    def test_timeout(self, mock_post):
        """Should return failed on timeout."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus
        import requests as real_requests

        # Mock timeout
        mock_post.side_effect = real_requests.exceptions.Timeout("timeout")

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="000001")

        assert result.status == ProviderStatus.FAILED
        assert "timeout" in result.error_message.lower()

    @patch("requests.post")
    def test_connection_error(self, mock_post):
        """Should return failed on connection error."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus
        import requests as real_requests

        # Mock connection error
        mock_post.side_effect = real_requests.exceptions.ConnectionError("connection failed")

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="000001")

        assert result.status == ProviderStatus.FAILED
        assert "connection" in result.error_message.lower()

    @patch("requests.post")
    def test_invalid_json(self, mock_post):
        """Should return failed on invalid JSON."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus

        # Mock invalid JSON response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"not json"
        mock_post.return_value = mock_response

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="000001")

        assert result.status == ProviderStatus.FAILED
        assert "json" in result.error_message.lower()


class TestCninfoPageSize:
    """Test page_size handling."""

    @patch("requests.post")
    def test_page_size_truncation(self, mock_post):
        """Should truncate page_size > 30."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(MOCK_CNINFO_RESPONSE).encode("gbk")
        mock_post.return_value = mock_response

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="000001", page_size=50)

        # Check warning
        assert any("truncated" in w.lower() for w in result.warnings)


class TestCninfoNoCookies:
    """Test that no cookies are sent."""

    @patch("requests.post")
    def test_no_cookies_sent(self, mock_post):
        """Should not send cookies."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(MOCK_CNINFO_RESPONSE).encode("gbk")
        mock_post.return_value = mock_response

        provider = CninfoProvider()
        provider.fetch("announcement", ticker="000001", org_id="gssz0000001")

        # Check that no cookies were sent
        call_kwargs = mock_post.call_args
        headers = call_kwargs[1].get("headers", {})
        assert "Cookie" not in headers
        assert "cookie" not in headers


class TestCninfoRawPayload:
    """Test raw payload saving."""

    @patch("requests.post")
    def test_raw_payload_saved(self, mock_post, tmp_path):
        """Should save raw payload."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.raw_store import RawPayloadStore

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(MOCK_CNINFO_RESPONSE).encode("gbk")
        mock_post.return_value = mock_response

        store = RawPayloadStore(base_dir=tmp_path)
        provider = CninfoProvider(raw_store=store)
        result = provider.fetch("announcement", ticker="000001", org_id="gssz0000001")

        assert result.raw_payload_path is not None
        assert Path(result.raw_payload_path).exists()


class TestCninfoNoBuySellFields:
    """Test that no buy/sell fields are present."""

    @patch("requests.post")
    def test_no_buy_sell_in_result(self, mock_post):
        """Should not contain buy/sell fields."""
        from tradingagents.markets.cn_stock.data_providers.cninfo_provider import (
            CninfoProvider,
        )

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(MOCK_CNINFO_RESPONSE).encode("gbk")
        mock_post.return_value = mock_response

        provider = CninfoProvider()
        result = provider.fetch("announcement", ticker="000001", org_id="gssz0000001")

        result_dict = result.to_dict()
        assert "buy" not in result_dict
        assert "sell" not in result_dict


class TestCninfoConfig:
    """Test configuration."""

    def test_config_status_experimental(self):
        """cninfo should be experimental in config."""
        import yaml

        config_path = PROJECT_ROOT / "config" / "cn_stock_providers.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        cninfo_config = config["providers"]["cninfo"]
        assert cninfo_config["status"] == "experimental"
        assert "announcement" in cninfo_config["datasets"]

    def test_config_max_concurrency(self):
        """cninfo should have max_concurrency=1."""
        import yaml

        config_path = PROJECT_ROOT / "config" / "cn_stock_providers.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        cninfo_config = config["providers"]["cninfo"]
        assert cninfo_config["concurrency"]["max_concurrency"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
