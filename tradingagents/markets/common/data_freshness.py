"""Data Freshness Guard.

System-level infrastructure for checking data freshness across all markets
and report types. This module does NOT fetch data - it only checks status
and determines whether reports can be generated.

IMPORTANT:
- Data Freshness Guard is a system-level infrastructure component.
- It does NOT fetch data, only checks status.
- All formal reports MUST check freshness before generation.
- If data is stale/missing/failed, reports must degrade or block.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .data_status import (
    DataFreshStatus,
    DataStatus,
    ReportFreshnessResult,
    ReportOverallStatus,
)


# Default config path
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "data_freshness.yaml"


class DataFreshnessGuard:
    """Guard for checking data freshness before report generation.

    Usage:
        guard = DataFreshnessGuard()
        guard.load_config()

        # Create data statuses
        statuses = [
            DataStatus(
                dataset_name="realtime_quote",
                market="cn_stock",
                source="mootdx",
                status=DataFreshStatus.FRESH,
                fetched_at=datetime.now(),
                max_age_seconds=120,
                required=True,
            ),
            # ... more statuses
        ]

        # Check freshness
        result = guard.check_report_freshness("cn_stock", "pre_close_report", statuses)

        if result.can_generate_strong_conclusion:
            # Generate full report
            pass
        else:
            # Generate degraded report
            pass
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize DataFreshnessGuard.

        Args:
            config_path: Path to data_freshness.yaml. If None, uses default.
        """
        self._config_path = config_path or _DEFAULT_CONFIG_PATH
        self._config: Dict[str, Any] = {}

    def load_config(self, path: Optional[Path] = None) -> None:
        """Load freshness configuration from YAML file.

        Args:
            path: Optional override for config path.

        Raises:
            FileNotFoundError: If config file not found.
            yaml.YAMLError: If config file is invalid.
        """
        config_path = path or self._config_path
        if not config_path.exists():
            raise FileNotFoundError(f"Freshness config not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f) or {}

    def get_report_rules(self, market: str, report_type: str) -> Dict[str, Any]:
        """Get freshness rules for a specific market and report type.

        Args:
            market: Market identifier (e.g., "cn_stock")
            report_type: Report type (e.g., "pre_close_report")

        Returns:
            Dictionary of dataset rules.
        """
        market_config = self._config.get(market, {})
        report_config = market_config.get(report_type, {})
        return report_config

    def check_dataset_status(
        self,
        dataset_status: DataStatus,
        rule: Dict[str, Any],
        now: Optional[datetime] = None,
    ) -> DataStatus:
        """Check a single dataset against its freshness rule.

        Args:
            dataset_status: Current status of the dataset.
            rule: Freshness rule from config.
            now: Current time (for testing). If None, uses datetime.now().

        Returns:
            Updated DataStatus with freshness assessment.
        """
        if now is None:
            now = datetime.now()

        # If already failed, keep failed
        if dataset_status.status == DataFreshStatus.FAILED:
            return dataset_status

        # If already missing
        if dataset_status.status == DataFreshStatus.MISSING:
            if rule.get("required", False):
                dataset_status.status = DataFreshStatus.MISSING
            return dataset_status

        # Get max_age_seconds from rule
        max_age = rule.get("max_age_seconds")

        # If no time-based check (null), just track that data exists
        if max_age is None:
            if dataset_status.fetched_at is None and dataset_status.as_of_time is None:
                dataset_status.status = DataFreshStatus.UNKNOWN
            else:
                dataset_status.status = DataFreshStatus.FRESH
            return dataset_status

        # Check if fetched_at exists
        if dataset_status.fetched_at is None:
            if rule.get("required", False):
                dataset_status.status = DataFreshStatus.MISSING
            else:
                dataset_status.status = DataFreshStatus.MISSING
            return dataset_status

        # Check age
        age = (now - dataset_status.fetched_at).total_seconds()
        if age > max_age:
            dataset_status.status = DataFreshStatus.STALE
        else:
            dataset_status.status = DataFreshStatus.FRESH

        return dataset_status

    def check_report_freshness(
        self,
        market: str,
        report_type: str,
        dataset_statuses: List[DataStatus],
        now: Optional[datetime] = None,
    ) -> ReportFreshnessResult:
        """Check freshness for all datasets required by a report.

        Args:
            market: Market identifier.
            report_type: Report type.
            dataset_statuses: List of current dataset statuses.
            now: Current time (for testing). If None, uses datetime.now().

        Returns:
            ReportFreshnessResult with overall assessment.
        """
        if now is None:
            now = datetime.now()

        rules = self.get_report_rules(market, report_type)

        result = ReportFreshnessResult(
            market=market,
            report_type=report_type,
            checked_at=now,
        )

        # Check each dataset against its rule
        for status in dataset_statuses:
            rule = rules.get(status.dataset_name, {})
            if not rule:
                # No rule for this dataset, treat as optional unknown
                result.dataset_statuses.append(status)
                result.warnings.append(f"No freshness rule for dataset: {status.dataset_name}")
                continue

            # Apply rule
            checked_status = self.check_dataset_status(status, rule, now)
            result.dataset_statuses.append(checked_status)

            # Check if this blocks the report
            is_required = rule.get("required", False)
            if is_required and checked_status.status in (
                DataFreshStatus.MISSING,
                DataFreshStatus.FAILED,
                DataFreshStatus.STALE,
            ):
                reason = self._build_blocking_reason(checked_status)
                result.blocking_reasons.append(reason)

            # Check if this blocks strong conclusion
            if checked_status.status in (
                DataFreshStatus.MISSING,
                DataFreshStatus.FAILED,
                DataFreshStatus.STALE,
            ):
                # Special handling for announcement
                if checked_status.dataset_name == "announcement" and is_required:
                    result.blocking_reasons.append(
                        "公告层数据不可用，不能声称'无重大利空'"
                    )
                # Special handling for key market data
                elif checked_status.dataset_name in (
                    "realtime_quote", "minute_kline", "sector_data", "limit_up_pool"
                ) and is_required:
                    result.blocking_reasons.append(
                        f"关键行情数据 {checked_status.dataset_name} 不可用，不能生成强结论"
                    )

            # Add warnings for non-required stale/missing
            if not is_required and checked_status.status in (
                DataFreshStatus.MISSING,
                DataFreshStatus.FAILED,
                DataFreshStatus.STALE,
            ):
                result.warnings.append(
                    f"可选数据 {checked_status.dataset_name} 状态: {checked_status.status.value}"
                )

        # Determine overall status
        result = self._determine_overall_status(result)

        return result

    def _build_blocking_reason(self, status: DataStatus) -> str:
        """Build a human-readable blocking reason."""
        if status.status == DataFreshStatus.MISSING:
            return f"必需数据 {status.dataset_name} 缺失"
        elif status.status == DataFreshStatus.FAILED:
            return f"必需数据 {status.dataset_name} 获取失败: {status.error_message or '未知错误'}"
        elif status.status == DataFreshStatus.STALE:
            age_str = ""
            if status.fetched_at:
                age = (datetime.now() - status.fetched_at).total_seconds()
                age_str = f"，数据已过期 {age:.0f} 秒"
            return f"必需数据 {status.dataset_name} 过期{age_str}"
        return f"必需数据 {status.dataset_name} 状态异常: {status.status.value}"

    def _determine_overall_status(self, result: ReportFreshnessResult) -> ReportFreshnessResult:
        """Determine overall status based on blocking reasons and warnings."""
        if result.blocking_reasons:
            # Check if any blocking reason prevents report generation entirely
            critical_blocks = [
                r for r in result.blocking_reasons
                if "缺失" in r or "失败" in r
            ]
            if critical_blocks:
                result.overall_status = ReportOverallStatus.BLOCKED
                result.can_generate_report = False
                result.can_generate_strong_conclusion = False
            else:
                result.overall_status = ReportOverallStatus.WARNING
                result.can_generate_strong_conclusion = False
        elif result.warnings:
            result.overall_status = ReportOverallStatus.WARNING
        else:
            result.overall_status = ReportOverallStatus.OK

        return result

    def can_generate_report(self, result: ReportFreshnessResult) -> bool:
        """Check if a report can be generated.

        Args:
            result: ReportFreshnessResult from check_report_freshness.

        Returns:
            True if report can be generated (even if degraded).
        """
        return result.can_generate_report

    def can_generate_strong_conclusion(self, result: ReportFreshnessResult) -> bool:
        """Check if strong conclusions can be drawn.

        Args:
            result: ReportFreshnessResult from check_report_freshness.

        Returns:
            True if strong conclusions are allowed.
        """
        return result.can_generate_strong_conclusion

    def build_status_summary(self, result: ReportFreshnessResult) -> str:
        """Build a human-readable status summary for report header.

        Args:
            result: ReportFreshnessResult from check_report_freshness.

        Returns:
            Formatted summary string.
        """
        lines = [
            "## 数据新鲜度检查",
            "",
            f"- 检查时间: {result.checked_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- 报告类型: {result.report_type}",
            f"- 整体状态: {result.overall_status.value}",
            f"- 可生成报告: {'是' if result.can_generate_report else '否'}",
            f"- 可生成强结论: {'是' if result.can_generate_strong_conclusion else '否'}",
            "",
        ]

        if result.blocking_reasons:
            lines.append("### 阻断原因")
            lines.append("")
            for reason in result.blocking_reasons:
                lines.append(f"- ❌ {reason}")
            lines.append("")

        if result.warnings:
            lines.append("### 警告")
            lines.append("")
            for warning in result.warnings:
                lines.append(f"- ⚠️ {warning}")
            lines.append("")

        lines.append("### 数据集状态")
        lines.append("")
        lines.append("| 数据集 | 状态 | 来源 | 最后更新 | 说明 |")
        lines.append("|--------|------|------|----------|------|")

        for status in result.dataset_statuses:
            fetched_str = "N/A"
            if status.fetched_at:
                fetched_str = status.fetched_at.strftime("%H:%M:%S")

            status_emoji = {
                DataFreshStatus.FRESH: "✅",
                DataFreshStatus.STALE: "⚠️",
                DataFreshStatus.MISSING: "❌",
                DataFreshStatus.FAILED: "❌",
                DataFreshStatus.PARTIAL: "⚠️",
                DataFreshStatus.UNKNOWN: "❓",
            }.get(status.status, "❓")

            note = status.error_message or ""
            if status.status == DataFreshStatus.STALE and status.fetched_at:
                age = (datetime.now() - status.fetched_at).total_seconds()
                note = f"过期 {age:.0f}秒"

            lines.append(
                f"| {status.dataset_name} | {status_emoji} {status.status.value} | "
                f"{status.source} | {fetched_str} | {note} |"
            )

        return "\n".join(lines)

    def auto_update_expired_datasets(
        self,
        dataset_statuses: List[DataStatus],
    ) -> List[DataStatus]:
        """Placeholder for auto-updating expired datasets.

        This method will be implemented when provider adapters are integrated.
        Currently returns statuses unchanged.

        Args:
            dataset_statuses: List of current dataset statuses.

        Returns:
            List of dataset statuses (unchanged in this version).
        """
        # TODO: Implement when provider adapters are integrated
        # Future implementation:
        # 1. Identify expired datasets
        # 2. Call appropriate provider adapter to refresh
        # 3. Update fetched_at and status
        # 4. Return updated statuses
        return dataset_statuses

    def generate_attention_pool_freshness(
        self,
        latest_trade_date: str,
        record_count: int,
        unique_ticker_count: int,
        generated_at: Optional[datetime] = None,
    ) -> DataStatus:
        """Generate freshness metadata for Attention Pool.

        Args:
            latest_trade_date: Latest trade date in the pool.
            record_count: Number of records in the pool.
            unique_ticker_count: Number of unique tickers.
            generated_at: When the pool was generated.

        Returns:
            DataStatus for Attention Pool.
        """
        if generated_at is None:
            generated_at = datetime.now()

        return DataStatus(
            dataset_name="attention_pool",
            market="cn_stock",
            source="local_builder",
            status=DataFreshStatus.FRESH,
            fetched_at=generated_at,
            as_of_time=generated_at,
            max_age_seconds=None,  # Not time-based
            required=False,
            metadata={
                "latest_trade_date": latest_trade_date,
                "record_count": record_count,
                "unique_ticker_count": unique_ticker_count,
            },
        )
