"""Tests for provider orchestration.

These tests verify orchestration logic including:
- ProviderRequest handling
- ProviderRole semantics
- Blocking/degradation/unknown rules
- Experimental provider handling
- Provider execution

All tests use mocks, no real network calls.
"""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.markets.cn_stock.data_providers.orchestrator import (
    ProviderAggregationDecision,
    ProviderOrchestrationResult,
    ProviderRequest,
    ProviderRole,
    run_provider_plan,
    run_provider_request,
)
from tradingagents.markets.cn_stock.data_providers.schema import (
    ProviderResult,
    ProviderStatus,
)


# ============================================================================
# Mock Registry
# ============================================================================


class MockRegistry:
    """Mock provider registry for testing."""

    def __init__(self):
        self._providers = {}
        self._configs = {}

    def register(self, name, provider, config=None):
        self._providers[name] = provider
        if config:
            self._configs[name] = config

    def get(self, name):
        return self._providers.get(name)

    def get_config(self, name):
        return self._configs.get(name)


# ============================================================================
# Tests
# ============================================================================


class TestProviderRequest:
    """Test ProviderRequest schema."""

    def test_create_request(self):
        """Should create request correctly."""
        request = ProviderRequest(
            provider_name="mootdx",
            dataset="daily_kline",
            params={"ticker": "600519.SH"},
            role=ProviderRole.PRIMARY_MARKET_DATA,
            required=True,
        )

        assert request.provider_name == "mootdx"
        assert request.dataset == "daily_kline"
        assert request.role == ProviderRole.PRIMARY_MARKET_DATA
        assert request.required is True

    def test_request_serialization(self):
        """Should serialize to dict."""
        request = ProviderRequest(
            provider_name="tencent",
            dataset="valuation",
            role=ProviderRole.SUPPLEMENTARY_DATA,
        )

        d = request.to_dict()
        assert d["provider_name"] == "tencent"
        assert d["role"] == "supplementary_data"


class TestProviderRole:
    """Test ProviderRole enum."""

    def test_all_roles(self):
        """Should have all required roles."""
        assert ProviderRole.PRIMARY_MARKET_DATA.value == "primary_market_data"
        assert ProviderRole.SUPPLEMENTARY_DATA.value == "supplementary_data"
        assert ProviderRole.DISCLOSURE_DATA.value == "disclosure_data"
        assert ProviderRole.ATTENTION_DATA.value == "attention_data"
        assert ProviderRole.UNKNOWN.value == "unknown"


class TestRunProviderRequest:
    """Test run_provider_request function."""

    def test_provider_not_found(self):
        """Should return failed when provider not found."""
        registry = MockRegistry()
        request = ProviderRequest(
            provider_name="nonexistent",
            dataset="test",
        )

        result = run_provider_request(request, registry)

        assert result.status == ProviderStatus.FAILED
        assert "not found" in result.error_message.lower()

    def test_experimental_provider_not_allowed(self):
        """Should skip experimental provider when not allowed."""
        registry = MockRegistry()
        mock_provider = MagicMock()
        registry.register("test_provider", mock_provider, {"status": "experimental", "enabled": True})

        request = ProviderRequest(
            provider_name="test_provider",
            dataset="test",
            allow_experimental=False,
        )

        result = run_provider_request(request, registry)

        assert result.status == ProviderStatus.SKIPPED
        assert "experimental" in result.error_message.lower()

    def test_experimental_provider_allowed(self):
        """Should run experimental provider when allowed."""
        registry = MockRegistry()
        mock_provider = MagicMock()
        mock_provider.fetch_and_normalize.return_value = ProviderResult(
            status=ProviderStatus.SUCCESS,
            data={"test": "data"},
        )
        registry.register("test_provider", mock_provider, {"status": "experimental", "enabled": True})

        request = ProviderRequest(
            provider_name="test_provider",
            dataset="test",
            allow_experimental=True,
        )

        result = run_provider_request(request, registry)

        assert result.status == ProviderStatus.SUCCESS

    def test_disabled_provider(self):
        """Should skip disabled provider."""
        registry = MockRegistry()
        mock_provider = MagicMock()
        registry.register("test_provider", mock_provider, {"enabled": False})

        request = ProviderRequest(
            provider_name="test_provider",
            dataset="test",
        )

        result = run_provider_request(request, registry)

        assert result.status == ProviderStatus.SKIPPED
        assert "disabled" in result.error_message.lower()

    def test_provider_exception(self):
        """Should return failed on provider exception."""
        registry = MockRegistry()
        mock_provider = MagicMock()
        mock_provider.fetch_and_normalize.side_effect = RuntimeError("Test error")
        registry.register("test_provider", mock_provider)

        request = ProviderRequest(
            provider_name="test_provider",
            dataset="test",
        )

        result = run_provider_request(request, registry)

        assert result.status == ProviderStatus.FAILED
        assert "Test error" in result.error_message


class TestPrimaryMarketData:
    """Test primary market data handling."""

    def test_primary_success(self):
        """Primary success should allow continue."""
        from tradingagents.markets.cn_stock.data_providers.aggregation import (
            aggregate_provider_results,
        )

        request = ProviderRequest(
            provider_name="mootdx",
            dataset="daily_kline",
            role=ProviderRole.PRIMARY_MARKET_DATA,
        )

        result = ProviderResult(
            provider_name="mootdx",
            dataset_name="daily_kline",
            status=ProviderStatus.SUCCESS,
        )

        decision = aggregate_provider_results(
            [request],
            {"mootdx:daily_kline": result},
        )

        assert decision.can_continue is True
        assert len(decision.blocked_by) == 0

    def test_primary_failed_blocks(self):
        """Primary failed should block."""
        from tradingagents.markets.cn_stock.data_providers.aggregation import (
            aggregate_provider_results,
        )

        request = ProviderRequest(
            provider_name="mootdx",
            dataset="daily_kline",
            role=ProviderRole.PRIMARY_MARKET_DATA,
        )

        result = ProviderResult(
            provider_name="mootdx",
            dataset_name="daily_kline",
            status=ProviderStatus.FAILED,
            error_message="Connection failed",
        )

        decision = aggregate_provider_results(
            [request],
            {"mootdx:daily_kline": result},
        )

        assert decision.can_continue is False
        assert len(decision.blocked_by) > 0

    def test_primary_empty_blocks(self):
        """Primary empty should block."""
        from tradingagents.markets.cn_stock.data_providers.aggregation import (
            aggregate_provider_results,
        )

        request = ProviderRequest(
            provider_name="mootdx",
            dataset="daily_kline",
            role=ProviderRole.PRIMARY_MARKET_DATA,
        )

        result = ProviderResult(
            provider_name="mootdx",
            dataset_name="daily_kline",
            status=ProviderStatus.EMPTY,
        )

        decision = aggregate_provider_results(
            [request],
            {"mootdx:daily_kline": result},
        )

        assert decision.can_continue is False
        assert len(decision.blocked_by) > 0

    def test_primary_partial_degrades(self):
        """Primary partial should degrade, not block."""
        from tradingagents.markets.cn_stock.data_providers.aggregation import (
            aggregate_provider_results,
        )

        request = ProviderRequest(
            provider_name="mootdx",
            dataset="daily_kline",
            role=ProviderRole.PRIMARY_MARKET_DATA,
        )

        result = ProviderResult(
            provider_name="mootdx",
            dataset_name="daily_kline",
            status=ProviderStatus.PARTIAL,
        )

        decision = aggregate_provider_results(
            [request],
            {"mootdx:daily_kline": result},
        )

        assert decision.can_continue is True
        assert len(decision.degraded_by) > 0


class TestSupplementaryData:
    """Test supplementary data handling."""

    def test_supplementary_failed_degrades(self):
        """Supplementary failed should degrade, not block."""
        from tradingagents.markets.cn_stock.data_providers.aggregation import (
            aggregate_provider_results,
        )

        request = ProviderRequest(
            provider_name="tencent",
            dataset="valuation",
            role=ProviderRole.SUPPLEMENTARY_DATA,
        )

        result = ProviderResult(
            provider_name="tencent",
            dataset_name="valuation",
            status=ProviderStatus.FAILED,
            error_message="Connection failed",
        )

        decision = aggregate_provider_results(
            [request],
            {"tencent:valuation": result},
        )

        assert decision.can_continue is True
        assert len(decision.degraded_by) > 0
        assert len(decision.blocked_by) == 0

    def test_supplementary_empty_degrades(self):
        """Supplementary empty should degrade, not block."""
        from tradingagents.markets.cn_stock.data_providers.aggregation import (
            aggregate_provider_results,
        )

        request = ProviderRequest(
            provider_name="tencent",
            dataset="valuation",
            role=ProviderRole.SUPPLEMENTARY_DATA,
        )

        result = ProviderResult(
            provider_name="tencent",
            dataset_name="valuation",
            status=ProviderStatus.EMPTY,
        )

        decision = aggregate_provider_results(
            [request],
            {"tencent:valuation": result},
        )

        assert decision.can_continue is True
        assert len(decision.degraded_by) > 0
        assert len(decision.blocked_by) == 0


class TestDisclosureData:
    """Test disclosure data handling."""

    def test_disclosure_empty_cannot_infer_no_negative(self):
        """Disclosure empty should add disclosure unknown."""
        from tradingagents.markets.cn_stock.data_providers.aggregation import (
            aggregate_provider_results,
        )

        request = ProviderRequest(
            provider_name="cninfo",
            dataset="announcement",
            role=ProviderRole.DISCLOSURE_DATA,
        )

        result = ProviderResult(
            provider_name="cninfo",
            dataset_name="announcement",
            status=ProviderStatus.EMPTY,
        )

        decision = aggregate_provider_results(
            [request],
            {"cninfo:announcement": result},
        )

        assert decision.can_continue is True  # Doesn't block
        assert len(decision.disclosure_unknowns) > 0
        assert "no major negative" in decision.disclosure_unknowns[0].lower()

    def test_disclosure_failed_cannot_infer_no_negative(self):
        """Disclosure failed should add disclosure unknown."""
        from tradingagents.markets.cn_stock.data_providers.aggregation import (
            aggregate_provider_results,
        )

        request = ProviderRequest(
            provider_name="cninfo",
            dataset="announcement",
            role=ProviderRole.DISCLOSURE_DATA,
        )

        result = ProviderResult(
            provider_name="cninfo",
            dataset_name="announcement",
            status=ProviderStatus.FAILED,
            error_message="Connection failed",
        )

        decision = aggregate_provider_results(
            [request],
            {"cninfo:announcement": result},
        )

        assert decision.can_continue is True  # Doesn't block
        assert len(decision.disclosure_unknowns) > 0


class TestMixedResults:
    """Test mixed result scenarios."""

    def test_primary_success_supplementary_failed(self):
        """Primary success + supplementary failed => can continue with degradation."""
        from tradingagents.markets.cn_stock.data_providers.aggregation import (
            aggregate_provider_results,
        )

        requests = [
            ProviderRequest(
                provider_name="mootdx",
                dataset="daily_kline",
                role=ProviderRole.PRIMARY_MARKET_DATA,
            ),
            ProviderRequest(
                provider_name="tencent",
                dataset="valuation",
                role=ProviderRole.SUPPLEMENTARY_DATA,
            ),
        ]

        results = {
            "mootdx:daily_kline": ProviderResult(
                provider_name="mootdx",
                dataset_name="daily_kline",
                status=ProviderStatus.SUCCESS,
            ),
            "tencent:valuation": ProviderResult(
                provider_name="tencent",
                dataset_name="valuation",
                status=ProviderStatus.FAILED,
            ),
        }

        decision = aggregate_provider_results(requests, results)

        assert decision.can_continue is True
        assert len(decision.blocked_by) == 0
        assert len(decision.degraded_by) > 0

    def test_primary_failed_supplementary_success(self):
        """Primary failed + supplementary success => cannot continue."""
        from tradingagents.markets.cn_stock.data_providers.aggregation import (
            aggregate_provider_results,
        )

        requests = [
            ProviderRequest(
                provider_name="mootdx",
                dataset="daily_kline",
                role=ProviderRole.PRIMARY_MARKET_DATA,
            ),
            ProviderRequest(
                provider_name="tencent",
                dataset="valuation",
                role=ProviderRole.SUPPLEMENTARY_DATA,
            ),
        ]

        results = {
            "mootdx:daily_kline": ProviderResult(
                provider_name="mootdx",
                dataset_name="daily_kline",
                status=ProviderStatus.FAILED,
            ),
            "tencent:valuation": ProviderResult(
                provider_name="tencent",
                dataset_name="valuation",
                status=ProviderStatus.SUCCESS,
            ),
        }

        decision = aggregate_provider_results(requests, results)

        assert decision.can_continue is False
        assert len(decision.blocked_by) > 0

    def test_mixed_with_disclosure(self):
        """Primary success + supplementary failed + disclosure empty => can continue."""
        from tradingagents.markets.cn_stock.data_providers.aggregation import (
            aggregate_provider_results,
        )

        requests = [
            ProviderRequest(
                provider_name="mootdx",
                dataset="daily_kline",
                role=ProviderRole.PRIMARY_MARKET_DATA,
            ),
            ProviderRequest(
                provider_name="tencent",
                dataset="valuation",
                role=ProviderRole.SUPPLEMENTARY_DATA,
            ),
            ProviderRequest(
                provider_name="cninfo",
                dataset="announcement",
                role=ProviderRole.DISCLOSURE_DATA,
            ),
        ]

        results = {
            "mootdx:daily_kline": ProviderResult(
                provider_name="mootdx",
                dataset_name="daily_kline",
                status=ProviderStatus.SUCCESS,
            ),
            "tencent:valuation": ProviderResult(
                provider_name="tencent",
                dataset_name="valuation",
                status=ProviderStatus.FAILED,
            ),
            "cninfo:announcement": ProviderResult(
                provider_name="cninfo",
                dataset_name="announcement",
                status=ProviderStatus.EMPTY,
            ),
        }

        decision = aggregate_provider_results(requests, results)

        assert decision.can_continue is True
        assert len(decision.blocked_by) == 0
        assert len(decision.degraded_by) > 0
        assert len(decision.disclosure_unknowns) > 0


class TestFreshnessSummary:
    """Test freshness summary building."""

    def test_freshness_summary_counts(self):
        """Should count all status types correctly."""
        from tradingagents.markets.cn_stock.data_providers.aggregation import (
            _build_freshness_summary,
        )

        results = {
            "a": ProviderResult(status=ProviderStatus.SUCCESS),
            "b": ProviderResult(status=ProviderStatus.SUCCESS),
            "c": ProviderResult(status=ProviderStatus.FAILED),
            "d": ProviderResult(status=ProviderStatus.EMPTY),
            "e": ProviderResult(status=ProviderStatus.PARTIAL),
            "f": ProviderResult(status=ProviderStatus.NOT_IMPLEMENTED),
        }

        summary = _build_freshness_summary(results)

        assert summary["total_requests"] == 6
        assert summary["success_count"] == 2
        assert summary["failed_count"] == 1
        assert summary["empty_count"] == 1
        assert summary["partial_count"] == 1
        assert summary["not_implemented_count"] == 1


class TestNoBuySellFields:
    """Test that no buy/sell fields are present."""

    def test_no_buy_sell_in_decision(self):
        """Decision should not contain buy/sell fields."""
        decision = ProviderAggregationDecision()
        d = decision.to_dict()
        assert "buy" not in d
        assert "sell" not in d
        assert "recommendation" not in d

    def test_no_buy_sell_in_orchestration_result(self):
        """Orchestration result should not contain buy/sell fields."""
        result = ProviderOrchestrationResult()
        d = result.to_dict()
        assert "buy" not in d
        assert "sell" not in d
        assert "recommendation" not in d


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
