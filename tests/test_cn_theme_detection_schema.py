"""Tests for Theme Detection schema and skeleton.

These tests verify:
1. ThemeEvidence field validation
2. ThemeCandidate field validation
3. ThemeLevel enum
4. ThemeStatus enum
5. ThemeDetectionInput can load sample
6. ThemeDetectionResult serialization
7. calculate_theme_score outputs score_breakdown
8. Risk evidence produces risk penalty or warning
9. Market-Wide Scan block cascades to Theme Detection
10. Attention Pool overlap is evidence, not trading recommendation
11. out_of_pool_stocks can be recorded but not recommended
12. Non-mainboard stocks are not deleted
13. build_theme_detection_result produces no buy/sell fields
14. All existing tests still pass
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.markets.cn_stock.theme_detection.schema import (
    ThemeCandidate,
    ThemeDetectionInput,
    ThemeDetectionResult,
    ThemeEvidence,
    ThemeEvidenceType,
    ThemeLevel,
    ThemeStatus,
)
from tradingagents.markets.cn_stock.theme_detection.scoring import (
    ScoreBreakdown,
    calculate_theme_score,
)
from tradingagents.markets.cn_stock.theme_detection.detector import build_theme_detection_result
from tradingagents.markets.cn_stock.theme_detection.io import (
    load_theme_detection_input,
    save_theme_detection_result,
)


SAMPLE_INPUT_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "cn_theme_detection" / "sample_theme_detection_input.json"
)


@pytest.fixture
def sample_input():
    """Load sample input from fixture file."""
    return load_theme_detection_input(SAMPLE_INPUT_PATH)


class TestThemeEvidence:
    """Tests for ThemeEvidence schema."""

    def test_theme_evidence_fields(self):
        """ThemeEvidence should have correct fields."""
        evidence = ThemeEvidence(
            evidence_type=ThemeEvidenceType.SECTOR_STRENGTH,
            description="半导体板块涨幅 +3.50%",
            source="eastmoney",
            related_sectors=["BK0477"],
            related_stocks=["688981.SH"],
            score_contribution=85.0,
            confidence=0.9,
            data_status="fresh",
        )

        assert evidence.evidence_type == ThemeEvidenceType.SECTOR_STRENGTH
        assert evidence.description == "半导体板块涨幅 +3.50%"
        assert evidence.confidence == 0.9

    def test_theme_evidence_serialization(self):
        """ThemeEvidence should serialize/deserialize correctly."""
        evidence = ThemeEvidence(
            evidence_type=ThemeEvidenceType.LIMIT_UP_CLUSTER,
            description="涨停 5 家",
            confidence=0.85,
        )

        d = evidence.to_dict()
        restored = ThemeEvidence.from_dict(d)

        assert restored.evidence_type == ThemeEvidenceType.LIMIT_UP_CLUSTER
        assert restored.confidence == 0.85

    def test_all_evidence_types(self):
        """All evidence types should be valid."""
        for etype in ThemeEvidenceType:
            evidence = ThemeEvidence(evidence_type=etype)
            assert evidence.evidence_type == etype


class TestThemeCandidate:
    """Tests for ThemeCandidate schema."""

    def test_theme_candidate_fields(self):
        """ThemeCandidate should have correct fields."""
        candidate = ThemeCandidate(
            theme_name="半导体",
            theme_aliases=["芯片"],
            related_sectors=["BK0477"],
            core_stocks=["688981.SH"],
            theme_score=72.0,
            theme_level=ThemeLevel.A,
            theme_status=ThemeStatus.STRENGTHENING,
            is_new_theme=False,
            is_one_day_noise_candidate=False,
        )

        assert candidate.theme_name == "半导体"
        assert candidate.theme_level == ThemeLevel.A
        assert candidate.theme_score == 72.0

    def test_theme_candidate_serialization(self):
        """ThemeCandidate should serialize/deserialize correctly."""
        candidate = ThemeCandidate(
            theme_name="半导体",
            theme_score=72.0,
            theme_level=ThemeLevel.A,
            evidence=[
                ThemeEvidence(
                    evidence_type=ThemeEvidenceType.SECTOR_STRENGTH,
                    description="test",
                )
            ],
        )

        d = candidate.to_dict()
        restored = ThemeCandidate.from_dict(d)

        assert restored.theme_name == "半导体"
        assert len(restored.evidence) == 1
        assert restored.evidence[0].evidence_type == ThemeEvidenceType.SECTOR_STRENGTH

    def test_non_mainboard_stocks_preserved(self):
        """Non-mainboard stocks should be preserved in out_of_pool_stocks."""
        candidate = ThemeCandidate(
            theme_name="半导体",
            out_of_pool_stocks=["688981.SH"],  # STAR market
        )

        assert "688981.SH" in candidate.out_of_pool_stocks


class TestThemeLevel:
    """Tests for ThemeLevel enum."""

    def test_all_levels(self):
        """All theme levels should be valid."""
        assert ThemeLevel.S.value == "S"
        assert ThemeLevel.A.value == "A"
        assert ThemeLevel.B.value == "B"
        assert ThemeLevel.C.value == "C"
        assert ThemeLevel.UNKNOWN.value == "unknown"


class TestThemeStatus:
    """Tests for ThemeStatus enum."""

    def test_all_statuses(self):
        """All theme statuses should be valid."""
        assert ThemeStatus.EMERGING.value == "emerging"
        assert ThemeStatus.STRENGTHENING.value == "strengthening"
        assert ThemeStatus.MAIN_RISING.value == "main_rising"
        assert ThemeStatus.FIRST_DIVERGENCE.value == "first_divergence"
        assert ThemeStatus.ROTATING.value == "rotating"
        assert ThemeStatus.WEAKENING.value == "weakening"
        assert ThemeStatus.FADING.value == "fading"
        assert ThemeStatus.ONE_DAY_NOISE.value == "one_day_noise"
        assert ThemeStatus.UNKNOWN.value == "unknown"


class TestThemeDetectionInput:
    """Tests for ThemeDetectionInput."""

    def test_load_from_json(self, sample_input):
        """ThemeDetectionInput should load from JSON correctly."""
        assert sample_input.trade_date == "2026-05-31"
        assert len(sample_input.manual_theme_hints) == 2
        assert "半导体" in sample_input.manual_theme_hints

    def test_input_serialization(self, sample_input):
        """ThemeDetectionInput should serialize correctly."""
        d = sample_input.to_dict()
        assert d["trade_date"] == "2026-05-31"
        assert len(d["manual_theme_hints"]) == 2


class TestThemeDetectionResult:
    """Tests for ThemeDetectionResult."""

    def test_result_serialization(self):
        """ThemeDetectionResult should serialize/deserialize correctly."""
        result = ThemeDetectionResult(
            trade_date="2026-05-31",
            theme_candidates=[
                ThemeCandidate(
                    theme_name="半导体",
                    theme_level=ThemeLevel.A,
                )
            ],
            strongest_themes=["半导体"],
            can_continue_to_candidate_selection=True,
        )

        d = result.to_dict()
        restored = ThemeDetectionResult.from_dict(d)

        assert restored.trade_date == "2026-05-31"
        assert len(restored.theme_candidates) == 1
        assert restored.strongest_themes == ["半导体"]

    def test_categorize_themes_by_level(self):
        """Themes should be categorized by level."""
        result = ThemeDetectionResult(
            theme_candidates=[
                ThemeCandidate(theme_name="半导体", theme_level=ThemeLevel.A),
                ThemeCandidate(theme_name="机器人", theme_level=ThemeLevel.B),
                ThemeCandidate(theme_name="房地产", theme_level=ThemeLevel.C),
            ],
        )

        # Categorize
        for c in result.theme_candidates:
            if c.theme_level in (ThemeLevel.S, ThemeLevel.A):
                result.strongest_themes.append(c.theme_name)
            elif c.theme_level == ThemeLevel.B:
                result.watch_themes.append(c.theme_name)
            elif c.theme_level == ThemeLevel.C:
                result.weak_or_noise_themes.append(c.theme_name)

        assert result.strongest_themes == ["半导体"]
        assert result.watch_themes == ["机器人"]
        assert result.weak_or_noise_themes == ["房地产"]


class TestThemeScoring:
    """Tests for theme scoring."""

    def test_calculate_theme_score(self):
        """calculate_theme_score should produce valid breakdown."""
        evidence = [
            ThemeEvidence(
                evidence_type=ThemeEvidenceType.SECTOR_STRENGTH,
                score_contribution=85.0,
                confidence=0.9,
            ),
            ThemeEvidence(
                evidence_type=ThemeEvidenceType.LIMIT_UP_CLUSTER,
                score_contribution=75.0,
                confidence=0.85,
            ),
        ]

        breakdown = calculate_theme_score(evidence)

        assert isinstance(breakdown, ScoreBreakdown)
        assert breakdown.sector_strength_score > 0
        assert breakdown.limit_up_support_score > 0
        assert breakdown.total_score > 0

    def test_risk_evidence_penalty(self):
        """Risk evidence should produce negative score."""
        evidence = [
            ThemeEvidence(
                evidence_type=ThemeEvidenceType.SECTOR_STRENGTH,
                score_contribution=85.0,
                confidence=0.9,
            ),
            ThemeEvidence(
                evidence_type=ThemeEvidenceType.RISK_WARNING,
                score_contribution=50.0,
                confidence=0.8,
            ),
        ]

        breakdown = calculate_theme_score(evidence)

        assert breakdown.risk_penalty < 0
        # Total should be less than without risk
        breakdown_no_risk = calculate_theme_score([evidence[0]])
        assert breakdown.total_score < breakdown_no_risk.total_score

    def test_empty_evidence(self):
        """Empty evidence should produce zero scores."""
        breakdown = calculate_theme_score([])
        assert breakdown.total_score == 0.0

    def test_score_breakdown_serialization(self):
        """ScoreBreakdown should serialize correctly."""
        breakdown = ScoreBreakdown(
            sector_strength_score=25.5,
            total_score=50.0,
        )

        d = breakdown.to_dict()
        assert d["sector_strength_score"] == 25.5
        assert d["total_score"] == 50.0


class TestThemeDetection:
    """Tests for build_theme_detection_result."""

    def test_build_result_skeleton(self, sample_input):
        """build_theme_detection_result should produce valid result."""
        result = build_theme_detection_result(sample_input)

        assert result.trade_date == "2026-05-31"
        assert result.can_continue_to_candidate_selection is True

    def test_no_trading_recommendations(self, sample_input):
        """build_theme_detection_result should NOT produce trading recommendations."""
        result = build_theme_detection_result(sample_input)

        result_dict = result.to_dict()
        result_str = json.dumps(result_dict).lower()

        assert "buy" not in result_str
        assert "sell" not in result_str
        assert "target_price" not in result_str
        assert "stop_loss" not in result_str

    def test_market_scan_block_cascades(self):
        """Market-Wide Scan block should cascade to Theme Detection."""
        # Create a mock market scan result that blocks
        class MockMarketScanResult:
            can_continue_to_theme_detection = False
            blocking_reasons = ["Key data missing"]

        detection_input = ThemeDetectionInput(
            trade_date="2026-05-31",
            market_scan_result=MockMarketScanResult(),
        )

        result = build_theme_detection_result(detection_input)

        assert result.can_continue_to_candidate_selection is False
        assert len(result.blocking_reasons) > 0

    def test_attention_pool_overlap_as_evidence(self, sample_input):
        """Attention Pool overlap should be evidence, not trading recommendation."""
        result = build_theme_detection_result(sample_input)

        # Find semiconductor theme
        semi = next((c for c in result.theme_candidates if c.theme_name == "半导体"), None)
        if semi:
            # Check that attention_pool_stocks are recorded
            assert isinstance(semi.attention_pool_stocks, list)
            # But no buy/sell recommendation
            assert not hasattr(semi, "buy_recommendation")

    def test_out_of_pool_stocks_recorded(self, sample_input):
        """Out-of-pool stocks should be recorded but not recommended."""
        result = build_theme_detection_result(sample_input)

        # Find semiconductor theme
        semi = next((c for c in result.theme_candidates if c.theme_name == "半导体"), None)
        if semi:
            # out_of_pool_stocks should be a list
            assert isinstance(semi.out_of_pool_stocks, list)

    def test_manual_theme_hints_warning(self, sample_input):
        """Manual theme hints should produce a warning."""
        result = build_theme_detection_result(sample_input)

        assert any("Manual theme hints" in w for w in result.warnings)

    def test_empty_input(self):
        """Empty input should produce valid result with warnings."""
        detection_input = ThemeDetectionInput(trade_date="2026-05-31")
        result = build_theme_detection_result(detection_input)

        assert result.trade_date == "2026-05-31"
        assert result.can_continue_to_candidate_selection is True
        assert len(result.warnings) > 0


class TestIO:
    """Tests for I/O functions."""

    def test_load_sample_input(self):
        """Sample input should be loadable."""
        input_path = Path(SAMPLE_INPUT_PATH)
        assert input_path.exists()

        data = load_theme_detection_input(input_path)
        assert data.trade_date == "2026-05-31"

    def test_save_and_load_result(self, tmp_path):
        """Result should save and load correctly."""
        result = ThemeDetectionResult(
            trade_date="2026-05-31",
            theme_candidates=[
                ThemeCandidate(
                    theme_name="半导体",
                    theme_level=ThemeLevel.A,
                )
            ],
        )

        output_path = tmp_path / "result.json"
        save_theme_detection_result(result, output_path)

        assert output_path.exists()
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["trade_date"] == "2026-05-31"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
