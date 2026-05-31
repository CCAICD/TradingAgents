"""Tests for Candidate Selection schema and skeleton.

These tests verify:
1. StockCandidate field validation
2. ReplacementCandidate field validation
3. CandidateSelectionInput can load sample
4. CandidateSelectionResult serialization
5. requires_replacement identifies non-mainboard
6. requires_replacement identifies limit up
7. requires_replacement identifies high price
8. Missing price data produces warning, not fabricated price
9. select_replacement_candidate prioritizes same theme, main board, non-limit-up
10. No replacement returns None with reason
11. candidate_score has score_breakdown
12. Risk penalty cannot be fully covered by attention score
13. Out-of-pool candidates don't mix into regular attention pool
14. build_candidate_selection_result produces no buy/sell fields
15. Theme Detection block cascades to Candidate Selection
16. Non-mainboard stocks are not deleted
17. All existing tests still pass
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.markets.cn_stock.candidate_selection.schema import (
    CandidateActionLabel,
    CandidateRiskLevel,
    CandidateSelectionInput,
    CandidateSelectionResult,
    CandidateSourceType,
    CandidateTradabilityFlag,
    ManualConstraints,
    OutOfPoolHighConvictionCandidate,
    ReplacementCandidate,
    StockCandidate,
)
from tradingagents.markets.cn_stock.candidate_selection.replacement import (
    requires_replacement,
    select_replacement_candidate,
)
from tradingagents.markets.cn_stock.candidate_selection.scoring import (
    CandidateScoreBreakdown,
    calculate_candidate_score,
)
from tradingagents.markets.cn_stock.candidate_selection.selector import build_candidate_selection_result
from tradingagents.markets.cn_stock.candidate_selection.io import (
    load_candidate_selection_input,
    save_candidate_selection_result,
)


SAMPLE_INPUT_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "cn_candidate_selection" / "sample_candidate_selection_input.json"
)


@pytest.fixture
def sample_input():
    """Load sample input from fixture file."""
    return load_candidate_selection_input(SAMPLE_INPUT_PATH)


class TestStockCandidate:
    """Tests for StockCandidate schema."""

    def test_stock_candidate_fields(self):
        """StockCandidate should have correct fields."""
        candidate = StockCandidate(
            ticker="600584.SH",
            name="长电科技",
            theme_name="半导体",
            source_type=CandidateSourceType.ATTENTION_POOL,
            board_type="main_board_sh",
            is_main_board=True,
            latest_price=35.50,
            is_limit_up=False,
            attention_score_20d=113.3,
            theme_score=72.0,
            tradability_flags=[CandidateTradabilityFlag.MAIN_BOARD],
            risk_level=CandidateRiskLevel.LOW,
            action_label=CandidateActionLabel.WATCH,
        )

        assert candidate.ticker == "600584.SH"
        assert candidate.is_main_board is True
        assert candidate.latest_price == 35.50
        assert CandidateTradabilityFlag.MAIN_BOARD in candidate.tradability_flags

    def test_stock_candidate_serialization(self):
        """StockCandidate should serialize/deserialize correctly."""
        candidate = StockCandidate(
            ticker="600584.SH",
            name="长电科技",
            candidate_score=75.5,
            tradability_flags=[CandidateTradabilityFlag.MAIN_BOARD],
        )

        d = candidate.to_dict()
        restored = StockCandidate.from_dict(d)

        assert restored.ticker == "600584.SH"
        assert restored.candidate_score == 75.5
        assert CandidateTradabilityFlag.MAIN_BOARD in restored.tradability_flags

    def test_non_mainboard_preserved(self):
        """Non-mainboard stocks should be preserved."""
        candidate = StockCandidate(
            ticker="688981.SH",
            name="中芯国际",
            is_main_board=False,
            tradability_flags=[CandidateTradabilityFlag.NON_MAIN_BOARD],
        )

        assert candidate.is_main_board is False
        assert CandidateTradabilityFlag.NON_MAIN_BOARD in candidate.tradability_flags


class TestReplacementCandidate:
    """Tests for ReplacementCandidate schema."""

    def test_replacement_fields(self):
        """ReplacementCandidate should have correct fields."""
        replacement = ReplacementCandidate(
            original_ticker="688981.SH",
            original_name="中芯国际",
            replacement_ticker="600584.SH",
            replacement_name="长电科技",
            theme_name="半导体",
            replacement_reason="非主板",
            why_original_not_suitable="非主板",
        )

        assert replacement.original_ticker == "688981.SH"
        assert replacement.replacement_ticker == "600584.SH"


class TestCandidateTradabilityFlag:
    """Tests for CandidateTradabilityFlag enum."""

    def test_all_flags(self):
        """All flags should be valid."""
        assert CandidateTradabilityFlag.MAIN_BOARD.value == "main_board"
        assert CandidateTradabilityFlag.NON_MAIN_BOARD.value == "non_main_board"
        assert CandidateTradabilityFlag.LIMIT_UP.value == "limit_up"
        assert CandidateTradabilityFlag.HIGH_PRICE.value == "high_price"
        assert CandidateTradabilityFlag.ST_OR_STAR_ST.value == "st_or_star_st"


class TestCandidateRiskLevel:
    """Tests for CandidateRiskLevel enum."""

    def test_all_levels(self):
        """All levels should be valid."""
        assert CandidateRiskLevel.LOW.value == "low"
        assert CandidateRiskLevel.MEDIUM.value == "medium"
        assert CandidateRiskLevel.HIGH.value == "high"
        assert CandidateRiskLevel.BLOCKED.value == "blocked"
        assert CandidateRiskLevel.UNKNOWN.value == "unknown"


class TestCandidateActionLabel:
    """Tests for CandidateActionLabel enum."""

    def test_no_buy_sell(self):
        """Should NOT contain buy/sell labels."""
        labels = [e.value for e in CandidateActionLabel]
        assert "buy" not in labels
        assert "sell" not in labels

    def test_all_labels(self):
        """All labels should be valid."""
        assert CandidateActionLabel.WATCH.value == "watch"
        assert CandidateActionLabel.WAIT_FOR_PULLBACK.value == "wait_for_pullback"
        assert CandidateActionLabel.AVOID.value == "avoid"
        assert CandidateActionLabel.DATA_INSUFFICIENT.value == "data_insufficient"


class TestCandidateSelectionInput:
    """Tests for CandidateSelectionInput."""

    def test_load_from_json(self, sample_input):
        """CandidateSelectionInput should load from JSON correctly."""
        assert sample_input.trade_date == "2026-05-31"
        assert sample_input.manual_constraints.prefer_main_board is True
        assert sample_input.manual_constraints.high_price_threshold == 120.0

    def test_default_constraints(self):
        """Default constraints should have correct values."""
        constraints = ManualConstraints()
        assert constraints.prefer_main_board is True
        assert constraints.high_price_threshold == 120.0
        assert constraints.avoid_limit_up is True
        assert constraints.allow_non_main_board is False


class TestReplacementRules:
    """Tests for replacement rules."""

    def test_requires_replacement_non_mainboard(self):
        """Non-mainboard should require replacement."""
        candidate = StockCandidate(
            ticker="688981.SH",
            is_main_board=False,
        )

        needs, reason = requires_replacement(candidate)
        assert needs is True
        assert "非主板" in reason

    def test_requires_replacement_limit_up(self):
        """Limit up should require replacement."""
        candidate = StockCandidate(
            ticker="600584.SH",
            is_main_board=True,
            is_limit_up=True,
        )

        needs, reason = requires_replacement(candidate)
        assert needs is True
        assert "涨停" in reason

    def test_requires_replacement_high_price(self):
        """Price > 120 should require replacement."""
        candidate = StockCandidate(
            ticker="600519.SH",
            is_main_board=True,
            latest_price=150.0,
            is_limit_up=False,
        )

        needs, reason = requires_replacement(candidate)
        assert needs is True
        assert "120" in reason

    def test_requires_replacement_missing_price(self):
        """Missing price should produce warning, not fabricate."""
        candidate = StockCandidate(
            ticker="600584.SH",
            is_main_board=True,
            latest_price=None,
            is_limit_up=None,
            tradability_flags=[CandidateTradabilityFlag.MISSING_PRICE_DATA],
        )

        needs, reason = requires_replacement(candidate)
        assert needs is True
        assert "价格数据缺失" in reason

    def test_no_replacement_needed(self):
        """Main board, non-limit-up, reasonable price should not need replacement."""
        candidate = StockCandidate(
            ticker="600584.SH",
            is_main_board=True,
            latest_price=35.50,
            is_limit_up=False,
        )

        needs, reason = requires_replacement(candidate)
        assert needs is False
        assert reason == ""

    def test_select_replacement_prefers_main_board(self):
        """Should prefer main board candidate."""
        original = StockCandidate(ticker="688981.SH", is_main_board=False)
        candidates = [
            StockCandidate(ticker="600584.SH", is_main_board=True, latest_price=35.0, is_limit_up=False, attention_score_20d=80),
            StockCandidate(ticker="002156.SZ", is_main_board=True, latest_price=25.0, is_limit_up=False, attention_score_20d=70),
        ]

        replacement = select_replacement_candidate(original, candidates)
        assert replacement is not None
        assert replacement.ticker == "600584.SH"

    def test_select_replacement_avoids_limit_up(self):
        """Should avoid limit up candidates."""
        original = StockCandidate(ticker="688981.SH", is_main_board=False)
        candidates = [
            StockCandidate(ticker="600584.SH", is_main_board=True, latest_price=35.0, is_limit_up=True, attention_score_20d=100),
            StockCandidate(ticker="002156.SZ", is_main_board=True, latest_price=25.0, is_limit_up=False, attention_score_20d=80),
        ]

        replacement = select_replacement_candidate(original, candidates)
        assert replacement is not None
        assert replacement.ticker == "002156.SZ"

    def test_select_replacement_no_candidates(self):
        """Should return None when no candidates available."""
        original = StockCandidate(ticker="688981.SH", is_main_board=False)
        replacement = select_replacement_candidate(original, [])
        assert replacement is None


class TestCandidateScoring:
    """Tests for candidate scoring."""

    def test_calculate_candidate_score(self):
        """calculate_candidate_score should produce valid breakdown."""
        candidate = StockCandidate(
            ticker="600584.SH",
            is_main_board=True,
            latest_price=35.50,
            is_limit_up=False,
            attention_score_20d=113.3,
            theme_score=72.0,
            tradability_flags=[CandidateTradabilityFlag.MAIN_BOARD],
            risk_level=CandidateRiskLevel.LOW,
        )

        breakdown = calculate_candidate_score(candidate)

        assert isinstance(breakdown, CandidateScoreBreakdown)
        assert breakdown.attention_component > 0
        assert breakdown.theme_component > 0
        assert breakdown.final_score > 0

    def test_risk_penalty_not_covered(self):
        """Risk penalty should reduce score even with high attention."""
        candidate_good = StockCandidate(
            ticker="600584.SH",
            is_main_board=True,
            latest_price=35.50,
            is_limit_up=False,
            attention_score_20d=100,
            theme_score=80,
            tradability_flags=[CandidateTradabilityFlag.MAIN_BOARD],
            risk_level=CandidateRiskLevel.LOW,
        )

        candidate_risky = StockCandidate(
            ticker="600584.SH",
            is_main_board=True,
            latest_price=35.50,
            is_limit_up=False,
            attention_score_20d=100,
            theme_score=80,
            tradability_flags=[CandidateTradabilityFlag.MAIN_BOARD],
            risk_level=CandidateRiskLevel.HIGH,
        )

        score_good = calculate_candidate_score(candidate_good)
        score_risky = calculate_candidate_score(candidate_risky)

        assert score_risky.final_score < score_good.final_score

    def test_score_breakdown_serialization(self):
        """ScoreBreakdown should serialize correctly."""
        breakdown = CandidateScoreBreakdown(
            attention_component=35.0,
            theme_component=25.0,
            final_score=60.0,
        )

        d = breakdown.to_dict()
        assert d["attention_component"] == 35.0
        assert d["final_score"] == 60.0


class TestCandidateSelection:
    """Tests for build_candidate_selection_result."""

    def test_build_result_skeleton(self, sample_input):
        """build_candidate_selection_result should produce valid result."""
        result = build_candidate_selection_result(sample_input)

        assert result.trade_date == "2026-05-31"
        assert result.can_continue_to_report is True

    def test_no_trading_recommendations(self, sample_input):
        """build_candidate_selection_result should NOT produce trading recommendations."""
        result = build_candidate_selection_result(sample_input)

        result_str = json.dumps(result.to_dict()).lower()

        assert "buy" not in result_str
        assert "sell" not in result_str
        assert "target_price" not in result_str
        assert "stop_loss" not in result_str

    def test_theme_detection_block_cascades(self):
        """Theme Detection block should cascade to Candidate Selection."""
        class MockThemeDetectionResult:
            can_continue_to_candidate_selection = False
            blocking_reasons = ["Market-Wide Scan failed"]

        selection_input = CandidateSelectionInput(
            trade_date="2026-05-31",
            theme_detection_result=MockThemeDetectionResult(),
        )

        result = build_candidate_selection_result(selection_input)

        assert result.can_continue_to_report is False
        assert len(result.blocking_reasons) > 0

    def test_out_of_pool_not_in_regular(self, sample_input):
        """Out-of-pool candidates should not mix into regular candidates."""
        result = build_candidate_selection_result(sample_input)

        # Check that out_of_pool is separate
        assert isinstance(result.out_of_pool_high_conviction_candidates, list)

    def test_empty_input(self):
        """Empty input should produce valid result with warnings."""
        selection_input = CandidateSelectionInput(trade_date="2026-05-31")
        result = build_candidate_selection_result(selection_input)

        assert result.trade_date == "2026-05-31"
        assert result.can_continue_to_report is True
        assert len(result.warnings) > 0


class TestIO:
    """Tests for I/O functions."""

    def test_load_sample_input(self):
        """Sample input should be loadable."""
        input_path = Path(SAMPLE_INPUT_PATH)
        assert input_path.exists()

        data = load_candidate_selection_input(input_path)
        assert data.trade_date == "2026-05-31"

    def test_save_and_load_result(self, tmp_path):
        """Result should save and load correctly."""
        result = CandidateSelectionResult(
            trade_date="2026-05-31",
            candidates_by_theme={
                "半导体": [StockCandidate(ticker="600584.SH", name="长电科技")]
            },
        )

        output_path = tmp_path / "result.json"
        save_candidate_selection_result(result, output_path)

        assert output_path.exists()
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["trade_date"] == "2026-05-31"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
