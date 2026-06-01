"""Tests for provider endpoint validation script.

These tests verify the validation script works correctly
without making real network calls.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestValidationScriptImport:
    """Test that validation script can be imported."""

    def test_script_can_be_imported(self):
        """Script should be importable."""
        from scripts.validate_provider_endpoint import validate_provider_endpoint

        assert callable(validate_provider_endpoint)


class TestNetworkSafety:
    """Test network safety features."""

    def test_default_no_network(self):
        """Should skip without --allow-network."""
        from scripts.validate_provider_endpoint import validate_provider_endpoint

        result = validate_provider_endpoint(
            provider="cninfo",
            dataset="announcement",
            symbol="000001",
            allow_network=False,
        )

        assert result["status"] == "skipped"
        assert "not allowed" in result["reason"].lower()

    def test_max_requests_validation(self):
        """Should reject max_requests > 5."""
        from scripts.validate_provider_endpoint import validate_provider_endpoint

        result = validate_provider_endpoint(
            provider="cninfo",
            dataset="announcement",
            symbol="000001",
            allow_network=True,
            max_requests=10,
        )

        assert result["status"] == "error"
        assert "max_requests" in result["error"]

    def test_max_requests_minimum(self):
        """Should reject max_requests < 1."""
        from scripts.validate_provider_endpoint import validate_provider_endpoint

        result = validate_provider_endpoint(
            provider="cninfo",
            dataset="announcement",
            symbol="000001",
            allow_network=True,
            max_requests=0,
        )

        assert result["status"] == "error"


class TestProviderValidation:
    """Test provider validation logic."""

    def test_not_implemented_provider(self):
        """Should return not_implemented for unknown providers."""
        from scripts.validate_provider_endpoint import validate_provider_endpoint

        result = validate_provider_endpoint(
            provider="mootdx",
            dataset="daily_kline",
            symbol="600519",
            allow_network=True,
        )

        assert result["status"] == "not_implemented"

    def test_result_includes_metadata(self):
        """Result should include provider/dataset/symbol."""
        from scripts.validate_provider_endpoint import validate_provider_endpoint

        result = validate_provider_endpoint(
            provider="cninfo",
            dataset="announcement",
            symbol="000001",
            allow_network=True,
        )

        # When network is allowed but no requests lib, should fail
        assert result["provider"] == "cninfo"
        assert result["dataset"] == "announcement"
        assert result["symbol"] == "000001"


class TestCninfoEndpointConfig:
    """Test Cninfo endpoint configuration."""

    def test_cninfo_endpoint_exists(self):
        """Cninfo endpoint should be configured."""
        from scripts.validate_provider_endpoint import ENDPOINT_CONFIGS

        assert "cninfo" in ENDPOINT_CONFIGS
        assert "announcement" in ENDPOINT_CONFIGS["cninfo"]

    def test_cninfo_endpoint_url(self):
        """Cninfo endpoint URL should be correct."""
        from scripts.validate_provider_endpoint import ENDPOINT_CONFIGS

        config = ENDPOINT_CONFIGS["cninfo"]["announcement"]
        assert "cninfo.com.cn" in config["url"]
        assert "hisAnnouncement" in config["url"]

    def test_cninfo_endpoint_method(self):
        """Cninfo endpoint should use POST."""
        from scripts.validate_provider_endpoint import ENDPOINT_CONFIGS

        config = ENDPOINT_CONFIGS["cninfo"]["announcement"]
        assert config["method"] == "POST"

    def test_cninfo_endpoint_headers(self):
        """Cninfo endpoint should have required headers."""
        from scripts.validate_provider_endpoint import ENDPOINT_CONFIGS

        config = ENDPOINT_CONFIGS["cninfo"]["announcement"]
        headers = config.get("headers", {})
        assert "User-Agent" in headers
        assert "Content-Type" in headers


class TestNoBuySellFields:
    """Test that no buy/sell fields are present."""

    def test_no_buy_sell_in_result(self):
        """Should not contain buy/sell fields."""
        from scripts.validate_provider_endpoint import validate_provider_endpoint

        result = validate_provider_endpoint(
            provider="cninfo",
            dataset="announcement",
            symbol="000001",
            allow_network=False,
        )

        assert "buy" not in result
        assert "sell" not in result


class TestRawDirectory:
    """Test raw directory handling."""

    def test_raw_dir_parameter(self):
        """Should accept raw_dir parameter."""
        from scripts.validate_provider_endpoint import validate_provider_endpoint

        result = validate_provider_endpoint(
            provider="cninfo",
            dataset="announcement",
            symbol="000001",
            allow_network=False,
            raw_dir=Path("/tmp/test_raw"),
        )

        assert result["status"] == "skipped"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
