"""Tests for Data Freshness Guard.

These tests verify:
1. Fresh data passes check
2. Stale required data blocks strong conclusion
3. Missing required data blocks report/strong conclusion
4. Failed required data blocks report/strong conclusion
5. Missing optional data produces warning
6. Failed optional data produces warning
7. realtime_quote stale blocks strong conclusion
8. announcement failure blocks "no major negative" conclusion
9. max_age_seconds=null doesn't check time-based expiry
10. build_status_summary produces readable output
11. auto_update placeholder doesn't call external APIs
12. Existing hotlist tests still pass
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.markets.common.data_status import (
    DataFreshStatus,
    DataStatus,
    ReportFreshnessResult,
    ReportOverallStatus,
)
from tradingagents.markets.common.data_freshness import DataFreshnessGuard


@pytest.fixture
def guard():
    """Create a DataFreshnessGuard with loaded config."""
    g = DataFreshnessGuard()
    g.load_config()
    return g


@pytest.fixture
def now():
    """Fixed time for testing."""
    return datetime(2026, 5, 31, 14, 50, 0)


class TestDataFreshnessGuard:
    """Tests for DataFreshnessGuard."""

    def test_fresh_data_passes(self, guard, now):
        """Fresh data should pass check."""
        status = DataStatus(
            dataset_name="realtime_quote",
            market="cn_stock",
            source="mootdx",
            status=DataFreshStatus.FRESH,
            fetched_at=now - timedelta(seconds=30),
            max_age_seconds=120,
            required=True,
        )

        result = guard.check_report_freshness(
            "cn_stock", "pre_close_report", [status], now
        )

        assert result.overall_status == ReportOverallStatus.OK
        assert result.can_generate_report is True
        assert result.can_generate_strong_conclusion is True

    def test_stale_required_blocks_strong_conclusion(self, guard, now):
        """Stale required data should block strong conclusion."""
        status = DataStatus(
            dataset_name="realtime_quote",
            market="cn_stock",
            source="mootdx",
            status=DataFreshStatus.STALE,
            fetched_at=now - timedelta(seconds=300),  # 5 minutes ago
            max_age_seconds=120,
            required=True,
        )

        result = guard.check_report_freshness(
            "cn_stock", "pre_close_report", [status], now
        )

        assert result.can_generate_strong_conclusion is False

    def test_missing_required_blocks_report(self, guard, now):
        """Missing required data should block report."""
        status = DataStatus(
            dataset_name="realtime_quote",
            market="cn_stock",
            source="mootdx",
            status=DataFreshStatus.MISSING,
            fetched_at=None,
            max_age_seconds=120,
            required=True,
        )

        result = guard.check_report_freshness(
            "cn_stock", "pre_close_report", [status], now
        )

        assert result.can_generate_report is False
        assert result.can_generate_strong_conclusion is False

    def test_failed_required_blocks_report(self, guard, now):
        """Failed required data should block report."""
        status = DataStatus(
            dataset_name="realtime_quote",
            market="cn_stock",
            source="mootdx",
            status=DataFreshStatus.FAILED,
            fetched_at=None,
            max_age_seconds=120,
            required=True,
            error_message="Connection timeout",
        )

        result = guard.check_report_freshness(
            "cn_stock", "pre_close_report", [status], now
        )

        assert result.can_generate_report is False
        assert result.can_generate_strong_conclusion is False

    def test_missing_optional_produces_warning(self, guard, now):
        """Missing optional data should produce warning, not block."""
        status = DataStatus(
            dataset_name="news",
            market="cn_stock",
            source="eastmoney",
            status=DataFreshStatus.MISSING,
            fetched_at=None,
            max_age_seconds=900,
            required=False,
        )

        result = guard.check_report_freshness(
            "cn_stock", "pre_close_report", [status], now
        )

        assert result.overall_status == ReportOverallStatus.WARNING
        assert result.can_generate_report is True
        assert result.can_generate_strong_conclusion is True
        assert len(result.warnings) > 0

    def test_failed_optional_produces_warning(self, guard, now):
        """Failed optional data should produce warning, not block."""
        status = DataStatus(
            dataset_name="news",
            market="cn_stock",
            source="eastmoney",
            status=DataFreshStatus.FAILED,
            fetched_at=None,
            max_age_seconds=900,
            required=False,
            error_message="API rate limited",
        )

        result = guard.check_report_freshness(
            "cn_stock", "pre_close_report", [status], now
        )

        assert result.overall_status == ReportOverallStatus.WARNING
        assert result.can_generate_report is True
        assert len(result.warnings) > 0

    def test_realtime_quote_stale_blocks_strong_conclusion(self, guard, now):
        """Stale realtime_quote should block strong conclusion."""
        status = DataStatus(
            dataset_name="realtime_quote",
            market="cn_stock",
            source="mootdx",
            status=DataFreshStatus.STALE,
            fetched_at=now - timedelta(seconds=300),
            max_age_seconds=120,
            required=True,
        )

        result = guard.check_report_freshness(
            "cn_stock", "pre_close_report", [status], now
        )

        assert result.can_generate_strong_conclusion is False
        assert any("关键行情数据" in r for r in result.blocking_reasons)

    def test_announcement_failure_blocks_no_negative_conclusion(self, guard, now):
        """Announcement failure should block 'no major negative' conclusion."""
        status = DataStatus(
            dataset_name="announcement",
            market="cn_stock",
            source="cninfo",
            status=DataFreshStatus.FAILED,
            fetched_at=None,
            max_age_seconds=3600,
            required=True,
            error_message="API timeout",
        )

        result = guard.check_report_freshness(
            "cn_stock", "pre_close_report", [status], now
        )

        assert result.can_generate_strong_conclusion is False
        assert any("无重大利空" in r for r in result.blocking_reasons)

    def test_null_max_age_no_time_check(self, guard, now):
        """max_age_seconds=null should not check time-based expiry."""
        status = DataStatus(
            dataset_name="manual_hotlist",
            market="cn_stock",
            source="manual_input",
            status=DataFreshStatus.UNKNOWN,
            fetched_at=now - timedelta(days=100),  # Very old
            max_age_seconds=None,
            required=False,
        )

        result = guard.check_report_freshness(
            "cn_stock", "pre_close_report", [status], now
        )

        # Should not be stale (no time check)
        dataset_result = result.dataset_statuses[0]
        assert dataset_result.status != DataFreshStatus.STALE

    def test_build_status_summary_readable(self, guard, now):
        """build_status_summary should produce readable output."""
        statuses = [
            DataStatus(
                dataset_name="realtime_quote",
                market="cn_stock",
                source="mootdx",
                status=DataFreshStatus.FRESH,
                fetched_at=now - timedelta(seconds=30),
                max_age_seconds=120,
                required=True,
            ),
            DataStatus(
                dataset_name="news",
                market="cn_stock",
                source="eastmoney",
                status=DataFreshStatus.MISSING,
                fetched_at=None,
                max_age_seconds=900,
                required=False,
            ),
        ]

        result = guard.check_report_freshness(
            "cn_stock", "pre_close_report", statuses, now
        )

        summary = guard.build_status_summary(result)

        assert "数据新鲜度检查" in summary
        assert "realtime_quote" in summary
        assert "news" in summary
        assert "✅" in summary
        assert "❌" in summary

    def test_auto_update_placeholder(self, guard):
        """auto_update placeholder should not call external APIs."""
        statuses = [
            DataStatus(
                dataset_name="realtime_quote",
                market="cn_stock",
                source="mootdx",
                status=DataFreshStatus.STALE,
                fetched_at=datetime.now() - timedelta(seconds=300),
                max_age_seconds=120,
                required=True,
            ),
        ]

        # Should not raise or call external APIs
        result = guard.auto_update_expired_datasets(statuses)

        # Returns unchanged
        assert len(result) == 1
        assert result[0].status == DataFreshStatus.STALE

    def test_report_freshness_with_multiple_datasets(self, guard, now):
        """Report freshness check should handle multiple datasets."""
        statuses = [
            DataStatus(
                dataset_name="realtime_quote",
                market="cn_stock",
                source="mootdx",
                status=DataFreshStatus.FRESH,
                fetched_at=now - timedelta(seconds=30),
                max_age_seconds=120,
                required=True,
            ),
            DataStatus(
                dataset_name="minute_kline",
                market="cn_stock",
                source="mootdx",
                status=DataFreshStatus.FRESH,
                fetched_at=now - timedelta(seconds=60),
                max_age_seconds=600,
                required=True,
            ),
            DataStatus(
                dataset_name="sector_data",
                market="cn_stock",
                source="tencent",
                status=DataFreshStatus.FRESH,
                fetched_at=now - timedelta(seconds=120),
                max_age_seconds=600,
                required=True,
            ),
            DataStatus(
                dataset_name="limit_up_pool",
                market="cn_stock",
                source="eastmoney",
                status=DataFreshStatus.FRESH,
                fetched_at=now - timedelta(seconds=180),
                max_age_seconds=300,
                required=True,
            ),
            DataStatus(
                dataset_name="announcement",
                market="cn_stock",
                source="cninfo",
                status=DataFreshStatus.FRESH,
                fetched_at=now - timedelta(seconds=300),
                max_age_seconds=3600,
                required=True,
            ),
        ]

        result = guard.check_report_freshness(
            "cn_stock", "pre_close_report", statuses, now
        )

        assert result.overall_status == ReportOverallStatus.OK
        assert result.can_generate_report is True
        assert result.can_generate_strong_conclusion is True

    def test_config_loading(self, guard):
        """Config should be loaded correctly."""
        rules = guard.get_report_rules("cn_stock", "pre_close_report")
        assert "realtime_quote" in rules
        assert rules["realtime_quote"]["required"] is True
        assert rules["realtime_quote"]["max_age_seconds"] == 120

    def test_attention_pool_freshness_generation(self, guard):
        """generate_attention_pool_freshness should create valid DataStatus."""
        status = guard.generate_attention_pool_freshness(
            latest_trade_date="2026-05-31",
            record_count=692,
            unique_ticker_count=142,
        )

        assert status.dataset_name == "attention_pool"
        assert status.market == "cn_stock"
        assert status.status == DataFreshStatus.FRESH
        assert status.metadata["latest_trade_date"] == "2026-05-31"
        assert status.metadata["record_count"] == 692


class TestDataStatus:
    """Tests for DataStatus model."""

    def test_data_status_serialization(self):
        """DataStatus should serialize/deserialize correctly."""
        now = datetime.now()
        status = DataStatus(
            dataset_name="test",
            market="cn_stock",
            source="test_source",
            status=DataFreshStatus.FRESH,
            fetched_at=now,
            as_of_time=now,
            max_age_seconds=120,
            required=True,
            metadata={"key": "value"},
        )

        d = status.to_dict()
        restored = DataStatus.from_dict(d)

        assert restored.dataset_name == "test"
        assert restored.market == "cn_stock"
        assert restored.status == DataFreshStatus.FRESH
        assert restored.required is True
        assert restored.metadata == {"key": "value"}


class TestReportFreshnessResult:
    """Tests for ReportFreshnessResult model."""

    def test_result_serialization(self):
        """ReportFreshnessResult should serialize/deserialize correctly."""
        result = ReportFreshnessResult(
            market="cn_stock",
            report_type="pre_close_report",
            overall_status=ReportOverallStatus.OK,
            can_generate_report=True,
            can_generate_strong_conclusion=True,
            blocking_reasons=[],
            warnings=["test warning"],
            dataset_statuses=[],
        )

        d = result.to_dict()
        restored = ReportFreshnessResult.from_dict(d)

        assert restored.market == "cn_stock"
        assert restored.report_type == "pre_close_report"
        assert restored.overall_status == ReportOverallStatus.OK
        assert restored.warnings == ["test warning"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
