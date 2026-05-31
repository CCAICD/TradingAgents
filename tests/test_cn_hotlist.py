"""Tests for CN Stock hotlist parser and Attention Pool.

These tests verify:
1. Parser can parse four platforms
2. Parser can identify rank, code, name
3. Parser handles missing name/platform correctly
4. Non-mainboard records are not filtered out
5. Legacy import data can be read by Attention Pool builder
6. Attention Pool uses only recent 20 trade days
7. Multi-platform resonance increases score
8. Consecutive appearance increases score
9. Repeated runs don't produce duplicate output
10. Import default_config still works
11. Board type inference works correctly
12. Score breakdown is consistent with final score
13. Top 50 explain can be generated
"""

import json
import sys
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.markets.cn_stock.hotlist.schema import (
    HotlistRecord,
    AttentionScoreConfig,
    AttentionPoolEntry,
    ScoreBreakdown,
    ScoreEvidence,
)
from tradingagents.markets.cn_stock.hotlist.parser import parse_hotlist_text
from tradingagents.markets.cn_stock.hotlist.normalizer import (
    normalize_record,
    normalize_legacy_record,
    infer_board_type,
)
from tradingagents.markets.cn_stock.hotlist.attention_pool import (
    build_attention_pool,
    generate_top50_explain,
)


class TestParser:
    """Tests for hotlist text parser."""

    def test_parse_four_platforms(self):
        """Parser should recognize all four platforms."""
        text = """
同花顺：
1. 600519 贵州茅台
2. 000001 平安银行

东方财富：
1. 300750 宁德时代

雪球：
1. 002594 比亚迪

通达信：
1. 601138 工业富联
"""
        valid, invalid = parse_hotlist_text(text, "2026-05-31")

        assert len(valid) == 5
        sources = {r.source for r in valid}
        assert sources == {"同花顺", "东方财富", "雪球", "通达信"}

    def test_parse_rank_code_name(self):
        """Parser should extract rank, code, and name."""
        text = """
同花顺：
1. 600519 贵州茅台
2. 000001 平安银行
3、300750 宁德时代
"""
        valid, invalid = parse_hotlist_text(text, "2026-05-31")

        assert len(valid) == 3
        assert valid[0].rank == 1
        assert valid[0].ticker == "600519.SH"
        assert valid[0].name == "贵州茅台"
        assert valid[1].rank == 2
        assert valid[2].rank == 3

    def test_parse_code_before_name(self):
        """Parser should handle code before name."""
        text = """
同花顺：
600519 贵州茅台
"""
        valid, invalid = parse_hotlist_text(text, "2026-05-31")
        assert len(valid) == 1
        assert valid[0].ticker == "600519.SH"
        assert valid[0].name == "贵州茅台"

    def test_parse_name_before_code(self):
        """Parser should handle name before code."""
        text = """
同花顺：
贵州茅台 600519
"""
        valid, invalid = parse_hotlist_text(text, "2026-05-31")
        assert len(valid) == 1
        assert valid[0].ticker == "600519.SH"
        assert valid[0].name == "贵州茅台"

    def test_missing_name_invalid(self):
        """Records with missing name should be invalid."""
        text = """
同花顺：
1. 600519
"""
        valid, invalid = parse_hotlist_text(text, "2026-05-31")
        assert len(valid) == 0
        assert len(invalid) == 1
        assert "Missing name" in invalid[0].parse_warnings

    def test_missing_platform_invalid(self):
        """Records with no platform detected should be invalid."""
        text = """
1. 600519 贵州茅台
"""
        valid, invalid = parse_hotlist_text(text, "2026-05-31")
        assert len(invalid) >= 1
        assert any("Platform not detected" in r.parse_warnings for r in invalid)

    def test_non_mainboard_preserved(self):
        """Non-mainboard records should NOT be filtered out."""
        text = """
同花顺：
1. 300750 宁德时代
2. 688981 中芯国际
3. 600519 贵州茅台
"""
        valid, invalid = parse_hotlist_text(text, "2026-05-31")
        assert len(valid) == 3

        # Check board types
        gem_record = next(r for r in valid if r.ticker.startswith("300"))
        star_record = next(r for r in valid if r.ticker.startswith("688"))
        main_record = next(r for r in valid if r.ticker.startswith("600"))

        assert gem_record.is_main_board is False
        assert gem_record.board_type == "chinext"
        assert star_record.is_main_board is False
        assert star_record.board_type == "star_market"
        assert main_record.is_main_board is True
        assert main_record.board_type == "main_board_sh"

    def test_date_from_text(self):
        """Parser should extract date from text if not provided."""
        text = """
2026-05-31
同花顺：
1. 600519 贵州茅台
"""
        valid, invalid = parse_hotlist_text(text)
        assert len(valid) == 1
        assert valid[0].trade_date == "2026-05-31"

    def test_no_date_error(self):
        """Parser should fail if no date can be determined."""
        text = """
同花顺：
1. 600519 贵州茅台
"""
        # Pass trade_date=None and text has no date
        valid, invalid = parse_hotlist_text(text, trade_date="nodate")
        # When date is invalid, records should be invalid
        assert len(invalid) >= 1


class TestNormalizer:
    """Tests for record normalizer."""

    def test_normalize_ticker(self):
        """Normalizer should add suffix to bare codes."""
        record = HotlistRecord(
            trade_date="2026-05-31",
            source="同花顺",
            ticker="600519",
            name="贵州茅台",
        )
        normalized = normalize_record(record)
        assert normalized.ticker == "600519.SH"

    def test_normalize_ticker_sz(self):
        """Normalizer should handle SZ suffix."""
        record = HotlistRecord(
            trade_date="2026-05-31",
            source="同花顺",
            ticker="000001",
            name="平安银行",
        )
        normalized = normalize_record(record)
        assert normalized.ticker == "000001.SZ"

    def test_normalize_legacy_record(self):
        """Normalizer should handle legacy format."""
        legacy = {
            "date": "2026-05-28",
            "source": "通达信",
            "ticker": "002185.SZ",
            "name": "华天科技",
            "main_board": True,
        }
        record = normalize_legacy_record(legacy)
        assert record.trade_date == "2026-05-28"
        assert record.source == "通达信"
        assert record.ticker == "002185.SZ"
        assert record.is_main_board is True
        assert record.source_project == "tradingagents-old"


class TestBoardTypeInference:
    """Tests for board type inference."""

    def test_main_board_sh(self):
        """SH main board codes should be inferred correctly."""
        board, is_main = infer_board_type("600519.SH")
        assert board == "main_board_sh"
        assert is_main is True

    def test_main_board_sz(self):
        """SZ main board codes should be inferred correctly."""
        board, is_main = infer_board_type("000001.SZ")
        assert board == "main_board_sz"
        assert is_main is True

    def test_chinext(self):
        """GEM codes should be inferred correctly."""
        board, is_main = infer_board_type("300750.SZ")
        assert board == "chinext"
        assert is_main is False

    def test_star_market(self):
        """STAR market codes should be inferred correctly."""
        board, is_main = infer_board_type("688981.SH")
        assert board == "star_market"
        assert is_main is False

    def test_bse(self):
        """BSE codes should be inferred correctly."""
        board, is_main = infer_board_type("430047.BJ")
        assert board == "beijing_stock_exchange"
        assert is_main is False

    def test_unknown(self):
        """Unknown codes should return unknown."""
        board, is_main = infer_board_type("999999.SH")
        assert board == "unknown"
        assert is_main is None

    def test_non_mainboard_not_filtered(self):
        """Non-mainboard stocks should NOT be filtered out."""
        records = [
            HotlistRecord(
                trade_date="2026-05-28",
                source="同花顺",
                rank=1,
                ticker="300750.SZ",
                name="宁德时代",
                board_type="chinext",
                is_main_board=False,
                parse_status="valid",
            ),
            HotlistRecord(
                trade_date="2026-05-28",
                source="同花顺",
                rank=2,
                ticker="600519.SH",
                name="贵州茅台",
                board_type="main_board_sh",
                is_main_board=True,
                parse_status="valid",
            ),
        ]

        pool = build_attention_pool(records)
        assert len(pool) == 2  # Both should be in pool
        assert any(e.ticker == "300750.SZ" for e in pool)


class TestAttentionPool:
    """Tests for Attention Pool builder."""

    def _make_records(self, data: list) -> list:
        """Helper to create records from simple data."""
        records = []
        for trade_date, source, rank, ticker, name in data:
            board, is_main = infer_board_type(ticker)
            records.append(HotlistRecord(
                trade_date=trade_date,
                source=source,
                rank=rank,
                ticker=ticker,
                name=name,
                board_type=board,
                is_main_board=is_main,
                parse_status="valid",
            ))
        return records

    def test_basic_pool_building(self):
        """Basic pool building should work."""
        records = self._make_records([
            ("2026-05-28", "同花顺", 1, "600519.SH", "贵州茅台"),
            ("2026-05-28", "同花顺", 2, "000001.SZ", "平安银行"),
            ("2026-05-27", "同花顺", 1, "600519.SH", "贵州茅台"),
        ])

        pool = build_attention_pool(records)
        assert len(pool) == 2

        # 贵州茅台 should rank higher (more appearances)
        assert pool[0].ticker == "600519.SH"
        assert pool[0].appear_days_20d == 2

    def test_multi_platform_resonance(self):
        """Multi-platform resonance should increase score."""
        records = self._make_records([
            ("2026-05-28", "同花顺", 1, "600519.SH", "贵州茅台"),
            ("2026-05-28", "东方财富", 1, "600519.SH", "贵州茅台"),
            ("2026-05-28", "雪球", 1, "600519.SH", "贵州茅台"),
            ("2026-05-28", "同花顺", 1, "000001.SZ", "平安银行"),
        ])

        pool = build_attention_pool(records)

        # 贵州茅台 has 3 sources, 平安银行 has 1
        maotai = next(e for e in pool if e.ticker == "600519.SH")
        pingan = next(e for e in pool if e.ticker == "000001.SZ")

        assert maotai.source_count_20d == 3
        assert pingan.source_count_20d == 1
        assert maotai.attention_score_20d > pingan.attention_score_20d

    def test_consecutive_days_bonus(self):
        """Consecutive appearance should increase score."""
        records = self._make_records([
            ("2026-05-28", "同花顺", 1, "600519.SH", "贵州茅台"),
            ("2026-05-27", "同花顺", 1, "600519.SH", "贵州茅台"),
            ("2026-05-26", "同花顺", 1, "600519.SH", "贵州茅台"),
            ("2026-05-28", "同花顺", 1, "000001.SZ", "平安银行"),
        ])

        pool = build_attention_pool(records)

        maotai = next(e for e in pool if e.ticker == "600519.SH")
        pingan = next(e for e in pool if e.ticker == "000001.SZ")

        assert maotai.consecutive_days == 3
        assert pingan.consecutive_days == 1
        assert maotai.attention_score_20d > pingan.attention_score_20d

    def test_window_limit(self):
        """Attention Pool should only use recent N days."""
        config = AttentionScoreConfig()
        config.WINDOW_TRADE_DAYS = 3

        records = self._make_records([
            ("2026-05-28", "同花顺", 1, "600519.SH", "贵州茅台"),
            ("2026-05-27", "同花顺", 1, "600519.SH", "贵州茅台"),
            ("2026-05-26", "同花顺", 1, "600519.SH", "贵州茅台"),
            ("2026-05-25", "同花顺", 1, "600519.SH", "贵州茅台"),  # Outside window
            ("2026-05-24", "同花顺", 1, "600519.SH", "贵州茅台"),  # Outside window
        ])

        pool = build_attention_pool(records, config, window_trade_days=3)
        maotai = pool[0]

        assert maotai.appear_days_20d == 3  # Only 3 days in window

    def test_non_mainboard_not_filtered(self):
        """Non-mainboard stocks should appear in pool."""
        records = self._make_records([
            ("2026-05-28", "同花顺", 1, "300750.SZ", "宁德时代"),  # GEM
            ("2026-05-28", "同花顺", 2, "688981.SH", "中芯国际"),  # STAR
            ("2026-05-28", "同花顺", 3, "600519.SH", "贵州茅台"),  # Main
        ])

        pool = build_attention_pool(records)
        assert len(pool) == 3  # All three should be in pool

        tickers = {e.ticker for e in pool}
        assert "300750.SZ" in tickers
        assert "688981.SH" in tickers
        assert "600519.SH" in tickers

    def test_empty_records(self):
        """Empty records should return empty pool."""
        pool = build_attention_pool([])
        assert pool == []

    def test_score_breakdown_consistency(self):
        """Score breakdown final_score should match attention_score_20d."""
        records = self._make_records([
            ("2026-05-28", "同花顺", 1, "600519.SH", "贵州茅台"),
            ("2026-05-28", "东方财富", 1, "600519.SH", "贵州茅台"),
            ("2026-05-27", "同花顺", 1, "600519.SH", "贵州茅台"),
        ])

        pool = build_attention_pool(records, include_breakdown=True)
        maotai = pool[0]

        assert maotai.score_breakdown is not None
        assert abs(maotai.score_breakdown.final_score - maotai.attention_score_20d) < 0.01

    def test_top50_explain_generation(self):
        """Top 50 explain should be generated correctly."""
        records = self._make_records([
            ("2026-05-28", "同花顺", 1, "600519.SH", "贵州茅台"),
            ("2026-05-28", "东方财富", 1, "600519.SH", "贵州茅台"),
        ])

        pool = build_attention_pool(records, include_breakdown=True)
        md_str, json_list = generate_top50_explain(pool)

        assert len(md_str) > 0
        assert len(json_list) == 1
        assert json_list[0]["ticker"] == "600519.SH"


class TestStockNameMap:
    """Tests for stock name mapping."""

    def test_name_map_exists(self):
        """Stock name map file should exist."""
        name_map_path = PROJECT_ROOT / "data" / "reference" / "stock_name_map.json"
        assert name_map_path.exists()

    def test_name_map_loadable(self):
        """Stock name map should be loadable."""
        name_map_path = PROJECT_ROOT / "data" / "reference" / "stock_name_map.json"
        with open(name_map_path, "r", encoding="utf-8") as f:
            name_map = json.load(f)
        assert len(name_map) > 0
        assert "600519" in name_map


class TestLegacyMerge:
    """Tests for legacy data merging logic."""

    def test_repaired_legacy_is_incremental(self):
        """Repaired legacy should be incremental, not replacing original."""
        # Load original legacy
        legacy_dir = PROJECT_ROOT / "data" / "manual_hotlists" / "legacy_import"
        legacy_file = legacy_dir / "structured" / "tradingagents-old" / "hotlist_legacy_tradingagents_old.jsonl"
        repaired_file = legacy_dir / "structured" / "tradingagents-old" / "hotlist_legacy_repaired.jsonl"

        if not legacy_file.exists() or not repaired_file.exists():
            pytest.skip("Legacy files not found")

        # Count records
        with open(legacy_file, "r", encoding="utf-8") as f:
            original_count = sum(1 for line in f if line.strip())
        with open(repaired_file, "r", encoding="utf-8") as f:
            repaired_count = sum(1 for line in f if line.strip())

        # Repaired should be a subset (the previously invalid ones)
        assert repaired_count > 0
        assert repaired_count < original_count

    def test_same_day_multi_platform_preserved(self):
        """Same stock on same day in different platforms should be preserved."""
        records = [
            HotlistRecord(
                trade_date="2026-05-28",
                source="同花顺",
                rank=1,
                ticker="600519.SH",
                name="贵州茅台",
                board_type="main_board_sh",
                is_main_board=True,
                parse_status="valid",
            ),
            HotlistRecord(
                trade_date="2026-05-28",
                source="东方财富",
                rank=1,
                ticker="600519.SH",
                name="贵州茅台",
                board_type="main_board_sh",
                is_main_board=True,
                parse_status="valid",
            ),
            HotlistRecord(
                trade_date="2026-05-28",
                source="雪球",
                rank=1,
                ticker="600519.SH",
                name="贵州茅台",
                board_type="main_board_sh",
                is_main_board=True,
                parse_status="valid",
            ),
        ]

        pool = build_attention_pool(records, include_breakdown=True)
        assert len(pool) == 1  # Only one stock
        maotai = pool[0]

        # But should have 3 sources (multi-platform resonance)
        assert maotai.source_count_20d == 3
        assert maotai.score_breakdown.resonance_bonus_sum > 0


class TestDefaultConfig:
    """Test that default config can still be imported."""

    def test_import_default_config(self):
        """Should be able to import default_config."""
        from tradingagents.default_config import DEFAULT_CONFIG

        assert "results_dir" in DEFAULT_CONFIG
        assert "data_cache_dir" in DEFAULT_CONFIG
        assert "memory_log_path" in DEFAULT_CONFIG


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
