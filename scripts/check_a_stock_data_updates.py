#!/usr/bin/env python3
"""
Check a-stock-data upstream for updates.

Usage:
    python scripts/check_a_stock_data_updates.py

Behavior:
    - Reads baseline from docs/external_sources/a_stock_data_baseline.json
    - Queries GitHub API for latest upstream status
    - Compares and generates update report
    - Does NOT download large files or execute upstream code
    - Does NOT modify current project business code

Output:
    - docs/external_sources/a_stock_data_update_check_latest.md
    - docs/external_sources/a_stock_data_update_checks/YYYY-MM-DD.md (if changes found)

IMPORTANT:
    - Upstream updates are for detection only, NOT automatic integration
    - All changes require human review before integration
    - Data interface changes are high-risk and cannot be silently updated
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

BASELINE_PATH = PROJECT_ROOT / "docs" / "external_sources" / "a_stock_data_baseline.json"
REPORTS_DIR = PROJECT_ROOT / "docs" / "external_sources"
CHECKS_DIR = REPORTS_DIR / "a_stock_data_update_checks"

REPO_API_URL = "https://api.github.com/repos/simonlin1212/a-stock-data"


def load_baseline() -> Dict[str, Any]:
    """Load baseline file."""
    if not BASELINE_PATH.exists():
        raise FileNotFoundError(f"Baseline file not found: {BASELINE_PATH}")

    with open(BASELINE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_github_json(url: str) -> Optional[Dict[str, Any]]:
    """Fetch JSON from GitHub API. Returns None on failure."""
    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "TradingAgents-AStock-UpdateChecker")

        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"Warning: Failed to fetch {url}: {e}")
        return None
    except Exception as e:
        print(f"Warning: Failed to fetch {url}: {e}")
        return None


def fetch_github_raw(url: str) -> Optional[str]:
    """Fetch raw text from GitHub. Returns None on failure."""
    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(url)
        req.add_header("User-Agent", "TradingAgents-AStock-UpdateChecker")

        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8")
    except urllib.error.URLError as e:
        print(f"Warning: Failed to fetch {url}: {e}")
        return None
    except Exception as e:
        print(f"Warning: Failed to fetch {url}: {e}")
        return None


def get_latest_commit() -> Optional[Dict[str, Any]]:
    """Get latest commit on main branch."""
    data = fetch_github_json(f"{REPO_API_URL}/commits/main")
    if not data:
        return None

    return {
        "sha": data.get("sha", ""),
        "message": data.get("commit", {}).get("message", ""),
        "date": data.get("commit", {}).get("committer", {}).get("date", ""),
        "author": data.get("commit", {}).get("author", {}).get("name", ""),
    }


def get_latest_release() -> Optional[Dict[str, Any]]:
    """Get latest release."""
    data = fetch_github_json(f"{REPO_API_URL}/releases/latest")
    if not data:
        return None

    return {
        "tag_name": data.get("tag_name", ""),
        "name": data.get("name", ""),
        "published_at": data.get("published_at", ""),
        "body": data.get("body", ""),
    }


def get_file_content(path: str) -> Optional[str]:
    """Get file content from GitHub."""
    url = f"https://raw.githubusercontent.com/simonlin1212/a-stock-data/main/{path}"
    return fetch_github_raw(url)


def assess_risk(changes: List[str], baseline: Dict[str, Any]) -> str:
    """Assess risk level of changes.

    Checks all changes against high risk first, then medium, then low.
    Returns the highest risk level found.
    """
    risk_rules = baseline.get("risk_rules", {})
    high_risk_keywords = risk_rules.get("high", [])
    medium_risk_keywords = risk_rules.get("medium", [])

    # Check all changes against high risk first
    for change_desc in changes:
        change_lower = change_desc.lower()
        for keyword in high_risk_keywords:
            if keyword.lower() in change_lower:
                return "high"

    # Then check all changes against medium risk
    for change_desc in changes:
        change_lower = change_desc.lower()
        for keyword in medium_risk_keywords:
            if keyword.lower() in change_lower:
                return "medium"

    return "low"


def check_for_updates(baseline: Dict[str, Any]) -> Dict[str, Any]:
    """Check for upstream updates.

    Returns:
        Dictionary with check results.
    """
    result = {
        "checked_at": datetime.now().isoformat(),
        "baseline_commit": baseline.get("audited_commit", "unknown"),
        "baseline_release": baseline.get("audited_release", "unknown"),
        "latest_commit": None,
        "latest_release": None,
        "has_updates": False,
        "changes": [],
        "risk_level": "low",
        "needs_re_audit": False,
        "details": {},
    }

    # Get latest commit
    print("Checking latest commit...")
    latest_commit = get_latest_commit()
    if latest_commit:
        result["latest_commit"] = latest_commit
        if latest_commit["sha"] != baseline.get("audited_commit"):
            result["has_updates"] = True
            result["changes"].append("Commit hash changed")
            result["details"]["commit_change"] = {
                "old": baseline.get("audited_commit", "unknown"),
                "new": latest_commit["sha"],
            }
    else:
        result["details"]["commit_check_error"] = "Failed to fetch latest commit"

    # Get latest release
    print("Checking latest release...")
    latest_release = get_latest_release()
    if latest_release:
        result["latest_release"] = latest_release
        if latest_release["tag_name"] != baseline.get("audited_release"):
            result["has_updates"] = True
            result["changes"].append(f"Release changed: {baseline.get('audited_release')} -> {latest_release['tag_name']}")
            result["details"]["release_change"] = {
                "old": baseline.get("audited_release", "unknown"),
                "new": latest_release["tag_name"],
            }
    else:
        result["details"]["release_check_error"] = "Failed to fetch latest release"

    # Check key files for changes
    files_to_check = ["SKILL.md", "README.md", "CHANGELOG.md", "LICENSE"]
    for filename in files_to_check:
        print(f"Checking {filename}...")
        content = get_file_content(filename)
        if content:
            result["details"][f"{filename}_available"] = True
            # We can't compare content directly without storing baseline content
            # But we can check if the file mentions certain keywords
            if filename == "SKILL.md":
                # Check for common interface change indicators
                indicators = ["deprecated", "removed", "breaking", "new endpoint", "replaced"]
                for indicator in indicators:
                    if indicator in content.lower():
                        result["changes"].append(f"SKILL.md contains keyword: {indicator}")
                        result["has_updates"] = True
            elif filename == "CHANGELOG.md":
                # Check for recent changes
                indicators = ["fix", "new", "removed", "deprecated", "breaking"]
                for indicator in indicators:
                    if indicator in content[:2000].lower():  # Only check recent entries
                        result["changes"].append(f"CHANGELOG.md recent entry contains: {indicator}")
                        result["has_updates"] = True
        else:
            result["details"][f"{filename}_error"] = "Failed to fetch"

    # Assess risk level
    if result["changes"]:
        result["risk_level"] = assess_risk(result["changes"], baseline)
        result["needs_re_audit"] = result["risk_level"] in ("medium", "high")

    return result


def generate_report(check_result: Dict[str, Any], baseline: Dict[str, Any]) -> str:
    """Generate markdown report from check result."""
    lines = [
        "# a-stock-data Upstream Update Check Report",
        "",
        f"> Checked at: {check_result['checked_at']}",
        "",
        "---",
        "",
        "## 一、检查结果",
        "",
        f"- 是否有更新: {'是' if check_result['has_updates'] else '否'}",
        f"- 风险等级: {check_result['risk_level'].upper()}",
        f"- 是否需要重新审计: {'是' if check_result['needs_re_audit'] else '否'}",
        "",
        "## 二、版本信息",
        "",
        "| 项目 | 基线 | 最新 |",
        "|------|------|------|",
        f"| Commit | {check_result['baseline_commit'][:8] if check_result['baseline_commit'] != 'unknown' else 'unknown'} | {check_result['latest_commit']['sha'][:8] if check_result['latest_commit'] else 'unknown'} |",
        f"| Release | {check_result['baseline_release']} | {check_result['latest_release']['tag_name'] if check_result['latest_release'] else 'unknown'} |",
        "",
    ]

    if check_result["changes"]:
        lines.extend([
            "## 三、变化列表",
            "",
        ])
        for change in check_result["changes"]:
            lines.append(f"- {change}")
        lines.append("")
    else:
        lines.extend([
            "## 三、变化列表",
            "",
            "无变化。",
            "",
        ])

    lines.extend([
        "## 四、风险评估",
        "",
    ])

    risk_explanations = {
        "low": "低风险：文档或非接口相关变化。可以安全更新审计记录。",
        "medium": "中风险：可能涉及接口修复或新数据源。建议重新审计。",
        "high": "高风险：接口实现或许可证变化。必须人工重新审计后才能接入或同步。",
    }
    lines.append(f"- {risk_explanations.get(check_result['risk_level'], '未知风险等级')}")
    lines.append("")

    lines.extend([
        "## 五、人工确认事项",
        "",
    ])

    if check_result["risk_level"] == "high":
        lines.extend([
            "- ⚠️ **高风险变更，需要人工重新审计**",
            "- 检查 SKILL.md 中哪些函数实现变化",
            "- 检查关键接口（巨潮/东财/腾讯/mootdx）是否受影响",
            "- 检查 LICENSE 是否变化",
            "- 决定是否需要更新本项目的 provider adapter",
            "",
        ])
    elif check_result["risk_level"] == "medium":
        lines.extend([
            "- ⚠️ **中风险变更，建议人工审查**",
            "- 检查 CHANGELOG 中提到的修复是否影响本项目",
            "- 决定是否需要更新审计记录",
            "",
        ])
    else:
        lines.extend([
            "- 低风险变更，可以更新审计记录",
            "- 不需要重新审计端点",
            "",
        ])

    lines.extend([
        "## 六、集成策略",
        "",
        "根据本项目原则：",
        "",
        "- ✅ 可以自动检查更新",
        "- ❌ 不允许自动合并上游代码",
        "- ❌ 不允许自动修改 provider",
        "- ❌ 不允许自动修改业务逻辑",
        "- ⚠️ 上游更新后只能生成审计报告和人工确认事项",
        "- ⚠️ 是否采用上游更新必须由用户 / ChatGPT / opencode 审查后决定",
        "",
        "---",
        "",
        "**文档结束。**",
        "",
        f"> 本文档由 check_a_stock_data_updates.py 自动生成于 {check_result['checked_at']}。",
    ])

    return "\n".join(lines)


def main():
    print("=== a-stock-data Upstream Update Check ===")
    print()

    # Load baseline
    print("Loading baseline...")
    try:
        baseline = load_baseline()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please create baseline file first.")
        sys.exit(1)

    print(f"Baseline: {baseline.get('audited_release', 'unknown')} ({baseline.get('audited_commit', 'unknown')[:8]})")
    print()

    # Check for updates
    print("Checking for updates...")
    result = check_for_updates(baseline)
    print()

    # Generate report
    print("Generating report...")
    report = generate_report(result, baseline)

    # Save latest report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    latest_path = REPORTS_DIR / "a_stock_data_update_check_latest.md"
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Saved latest report to: {latest_path}")

    # Save dated report if there are updates
    if result["has_updates"]:
        CHECKS_DIR.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        dated_path = CHECKS_DIR / f"{date_str}.md"
        with open(dated_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Saved dated report to: {dated_path}")

    # Print summary
    print()
    print("=== Summary ===")
    print(f"Has updates: {result['has_updates']}")
    print(f"Risk level: {result['risk_level']}")
    print(f"Needs re-audit: {result['needs_re_audit']}")
    if result["changes"]:
        print(f"Changes: {len(result['changes'])}")
        for change in result["changes"]:
            print(f"  - {change}")

    if result["risk_level"] == "high":
        print()
        print("⚠️ HIGH RISK: Human re-audit required before integration!")
        sys.exit(2)  # Exit with code 2 to indicate high risk
    elif result["has_updates"]:
        sys.exit(1)  # Exit with code 1 to indicate updates found
    else:
        print("No updates found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
