"""Tests for Market-Wide Scan schema and skeleton.

These tests verify:
1. MarketWideScanInput can be loaded from sample JSON
2. IndexSnapshot / SectorSnapshot / StrongStockSnapshot field validation
3. Missing key fields produce errors or warnings
4. Data Freshness Guard works with market_scan
5. Key data stale blocks theme detection
6. Optional data missing produces warning only
7. Non-mainboard strong stocks are not deleted
8. out_of_pool_candidates structure works
9. build_market_wide_scan_result produces no trading recommendations
10. Existing 61 tests still pass
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.markets.cn_stock.market_scan.schema import (
    IndexSnapshot,
    LimitUpPoolSnapshot,
    MarketBreadthSnapshot,
    MarketTemperature,
    MarketWideScanInput,
    MarketWideScanResult,
    OutOfPoolCandidateSignal,
    RiskLevel,
    SectorSnapshot,
    StrongStockSnapshot,
    ThemeCandidateSignal,
    ThemeCandidateStatus,
    TurnoverSnapshot,
)
from tradingagents.markets.cn_stock.market_scan.scan_result import build_market_wide_scan_result
from tradingagents.markets.cn_stock.market_scan.freshness import build_market_scan_freshness_status
from tradingagents.markets.cn_stock.market_scan.io import load_market_scan_input, save_market_scan_result
from tradingagents.markets.common.data_freshness import DataFreshnessGuard


SAMPLE_INPUT_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "cn_market_scan" / "sample_market_scan_input.json"
)


@pytest.fixture
def sample_input():
    """Load sample input from fixture file."""
    return load_market_scan_input(SAMPLE_INPUT_PATH)


@pytest.fixture
def guard():
    """Create a DataFreshnessGuard with loaded config."""
    g = DataFreshnessGuard()
    g.load_config()
    return g


class TestMarketWideScanInput:
    """Tests for MarketWideScanInput."""

    def test_load_from_json(self, sample_input):
        """MarketWideScanInput should load from JSON correctly."""
        assert sample_input.trade_date == "2026-05-31"
        assert len(sample_input.indexes) == 3
        assert sample_input.market_breadth is not None
        assert sample_input.turnover is not None
        assert len(sample_input.sectors) == 4
        assert len(sample_input.strong_stocks) == 3
        assert sample_input.limit_up_pool is not None

    def test_index_snapshot_fields(self, sample_input):
        """IndexSnapshot should have correct fields."""
        idx = sample_input.indexes[0]
        assert idx.index_code == "000001.SH"
        assert idx.index_name == "上证指数"
        assert idx.latest_price == 3250.50
        assert idx.pct_change == 0.85

    def test_sector_snapshot_fields(self, sample_input):
        """SectorSnapshot should have correct fields."""
        sector = sample_input.sectors[0]
        assert sector.sector_code == "BK0477"
        assert sector.sector_name == "半导体"
        assert sector.pct_change == 3.50
        assert len(sector.leading_stocks) == 2

    def test_strong_stock_fields(self, sample_input):
        """StrongStockSnapshot should have correct fields."""
        stock = sample_input.strong_stocks[0]
        assert stock.ticker == "600584.SH"
        assert stock.name == "长电科技"
        assert stock.is_limit_up is True
        assert stock.board_type == "main_board_sh"

    def test_non_mainboard_not_deleted(self, sample_input):
        """Non-mainboard stocks should be preserved."""
        # Find chinext stock
        chinext_stocks = [s for s in sample_input.strong_stocks if s.board_type == "chinext"]
        assert len(chinext_stocks) > 0
        assert chinext_stocks[0].ticker == "300750.SZ"

    def test_market_breadth_fields(self, sample_input):
        """MarketBreadthSnapshot should have correct fields."""
        breadth = sample_input.market_breadth
        assert breadth.up_count == 3200
        assert breadth.down_count == 1500
        assert breadth.limit_up_count == 88
        assert breadth.high_board_height == 4

    def test_turnover_fields(self, sample_input):
        """TurnoverSnapshot should have correct fields."""
        turnover = sample_input.turnover
        assert turnover.total_market_turnover == 10000.0
        assert turnover.turnover_change_vs_previous_day == 15.5

    def test_limit_up_pool_fields(self, sample_input):
        """LimitUpPoolSnapshot should have correct fields."""
        pool = sample_input.limit_up_pool
        assert pool.trade_date == "2026-05-31"
        assert len(pool.limit_up_stocks) == 4
        assert pool.high_board_height == 4

    def test_to_dict_roundtrip(self, sample_input):
        """to_dict should produce valid dict."""
        d = sample_input.to_dict()
        assert d["trade_date"] == "2026-05-31"
        assert len(d["indexes"]) == 3


class TestMarketWideScanResult:
    """Tests for MarketWideScanResult."""

    def test_build_result_skeleton(self, sample_input):
        """build_market_wide_scan_result should produce valid result."""
        result = build_market_wide_scan_result(sample_input)

        assert result.trade_date == "2026-05-31"
        assert result.market_temperature == MarketTemperature.UNKNOWN  # Not implemented yet
        assert result.risk_level == RiskLevel.UNKNOWN  # Not implemented yet
        assert result.can_continue_to_theme_detection is True
        assert len(result.theme_candidates) == 0  # Not implemented yet
        assert len(result.out_of_pool_candidates) == 0  # Not implemented yet

    def test_no_trading_recommendations(self, sample_input):
        """build_market_wide_scan_result should NOT produce trading recommendations."""
        result = build_market_wide_scan_result(sample_input)

        # No buy/sell/hold recommendations
        result_dict = result.to_dict()
        assert "buy" not in str(result_dict).lower()
        assert "sell" not in str(result_dict).lower()
        assert "target_price" not in str(result_dict).lower()
        assert "stop_loss" not in str(result_dict).lower()

    def test_breadth_summary_generated(self, sample_input):
        """Breadth summary should be generated from input."""
        result = build_market_wide_scan_result(sample_input)
        assert "上涨" in result.breadth_summary
        assert "涨停" in result.breadth_summary

    def test_turnover_summary_generated(self, sample_input):
        """Turnover summary should be generated from input."""
        result = build_market_wide_scan_result(sample_input)
        assert "成交额" in result.turnover_summary

    def test_strongest_weakest_sectors(self, sample_input):
        """Strongest and weakest sectors should be identified."""
        result = build_market_wide_scan_result(sample_input)
        assert len(result.strongest_sectors) > 0
        assert len(result.weakest_sectors) > 0

    def test_missing_breadth_blocks_detection(self):
        """Missing market breadth should block theme detection."""
        scan_input = MarketWideScanInput(
            trade_date="2026-05-31",
            indexes=[IndexSnapshot(
                index_code="000001.SH",
                index_name="上证指数",
                latest_price=3250,
                pct_change=0.5,
            )],
            # No market_breadth
            sectors=[SectorSnapshot(sector_name="test")],
            limit_up_pool=LimitUpPoolSnapshot(trade_date="2026-05-31"),
        )

        result = build_market_wide_scan_result(scan_input)
        assert result.can_continue_to_theme_detection is False
        assert any("market_breadth" in r for r in result.blocking_reasons)

    def test_missing_sectors_blocks_detection(self):
        """Missing sectors should block theme detection."""
        scan_input = MarketWideScanInput(
            trade_date="2026-05-31",
            indexes=[IndexSnapshot(
                index_code="000001.SH",
                index_name="上证指数",
                latest_price=3250,
                pct_change=0.5,
            )],
            market_breadth=MarketBreadthSnapshot(up_count=1000, down_count=500),
            # No sectors
            limit_up_pool=LimitUpPoolSnapshot(trade_date="2026-05-31"),
        )

        result = build_market_wide_scan_result(scan_input)
        assert result.can_continue_to_theme_detection is False


class TestOutOfPoolCandidate:
    """Tests for OutOfPoolCandidateSignal."""

    def test_out_of_pool_structure(self):
        """OutOfPoolCandidateSignal should have correct structure."""
        candidate = OutOfPoolCandidateSignal(
            ticker="688981.SH",
            name="中芯国际",
            theme_name="半导体",
            reason="板块最强标的",
            evidence=["涨停", "成交额放大"],
            in_attention_pool=False,
            requires_replacement=True,
        )

        d = candidate.to_dict()
        assert d["ticker"] == "688981.SH"
        assert d["in_attention_pool"] is False
        assert d["requires_replacement"] is True


class TestThemeCandidate:
    """Tests for ThemeCandidateSignal."""

    def test_theme_candidate_structure(self):
        """ThemeCandidateSignal should have correct structure."""
        candidate = ThemeCandidateSignal(
            theme_name="半导体",
            evidence_sectors=["BK0477"],
            evidence_stocks=["688981.SH", "002049.SZ"],
            sector_strength_score=85.0,
            status=ThemeCandidateStatus.STRONG_CANDIDATE,
        )

        d = candidate.to_dict()
        assert d["theme_name"] == "半导体"
        assert d["status"] == "strong_candidate"


class TestFreshnessIntegration:
    """Tests for freshness integration."""

    def test_freshness_status_generation(self):
        """build_market_scan_freshness_status should generate statuses."""
        statuses = build_market_scan_freshness_status(
            trade_date="2026-05-31",
            has_index_data=True,
            has_breadth_data=True,
            has_turnover_data=True,
            has_sector_data=True,
            has_limit_up_pool=True,
        )

        assert len(statuses) > 0
        # Required data should be FRESH
        for s in statuses:
            if s.required:
                assert s.status.value == "fresh"

    def test_freshness_blocks_when_missing(self, guard):
        """Missing required data should block via freshness guard."""
        statuses = build_market_scan_freshness_status(
            trade_date="2026-05-31",
            has_index_data=False,  # Missing required data
            has_breadth_data=True,
            has_turnover_data=True,
            has_sector_data=True,
            has_limit_up_pool=True,
        )

        result = guard.check_report_freshness(
            "cn_stock", "market_scan", statuses
        )

        # Should block because index_data is required and missing
        assert result.can_generate_report is False

    def test_optional_missing_only_warning(self, guard):
        """Missing optional data should produce warning only."""
        statuses = build_market_scan_freshness_status(
            trade_date="2026-05-31",
            has_index_data=True,
            has_breadth_data=True,
            has_turnover_data=True,
            has_sector_data=True,
            has_limit_up_pool=True,
            has_strong_stocks=False,  # Optional, missing
            has_attention_pool=False,  # Optional, missing
        )

        result = guard.check_report_freshness(
            "cn_stock", "market_scan", statuses
        )

        # Should not block because missing data is optional
        assert result.can_generate_report is True
        assert len(result.warnings) > 0


class TestIO:
    """Tests for I/O functions."""

    def test_load_and_save(self, sample_input, tmp_path):
        """Should load and save correctly."""
        output_path = tmp_path / "result.json"
        result = build_market_wide_scan_result(sample_input)
        save_market_scan_result(result, output_path)

        assert output_path.exists()
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["trade_date"] == "2026-05-31"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
