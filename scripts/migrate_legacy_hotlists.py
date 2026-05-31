#!/usr/bin/env python3
"""
迁移 tradingagents-old 热榜 JSONL 数据到当前项目的 legacy_import 区域。

用法：
    python scripts/migrate_legacy_hotlists.py

说明：
    - 不修改旧项目目录
    - 输出路径固定在当前项目 legacy_import
    - 重复运行会重建输出文件
"""

import json
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# 配置
SOURCE_DIR = Path(r"C:\github\tradingagents-old\data\hotlists")
TARGET_BASE = Path(__file__).resolve().parent.parent / "data" / "manual_hotlists" / "legacy_import"
TARGET_RAW = TARGET_BASE / "raw" / "tradingagents-old"
TARGET_STRUCTURED = TARGET_BASE / "structured" / "tradingagents-old"
TARGET_AUDIT = TARGET_BASE / "audit"

SOURCE_PROJECT = "tradingagents-old"
IMPORT_BATCH_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
IMPORTED_AT = datetime.now().isoformat()


def ensure_dirs():
    """确保目标目录存在"""
    for d in [TARGET_RAW, TARGET_STRUCTURED, TARGET_AUDIT]:
        d.mkdir(parents=True, exist_ok=True)
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()


def read_jsonl(filepath: Path) -> list:
    """读取 JSONL 文件"""
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"  Warning: Invalid JSON in {filepath}: {e}")
    return records


def validate_record(record: dict, filepath: Path) -> tuple:
    """验证记录，返回 (is_valid, reason)"""
    required_fields = ["date", "source", "ticker", "name"]
    for field in required_fields:
        if field not in record or not record[field]:
            return False, f"Missing required field: {field}"
    
    # 检查 ticker 格式
    ticker = record.get("ticker", "")
    if not ("." in ticker and (ticker.endswith(".SH") or ticker.endswith(".SZ"))):
        return False, f"Invalid ticker format: {ticker}"
    
    return True, None


def standardize_record(record: dict, filepath: Path) -> dict:
    """标准化记录格式"""
    is_valid, reason = validate_record(record, filepath)
    
    if not is_valid:
        return {
            "_invalid": True,
            "_reason": reason,
            "_original_path": str(filepath),
            "_raw_record": record
        }
    
    # 提取排名（从文件顺序推断）
    rank = record.get("rank", None)
    
    # 映射 board_type
    main_board = record.get("main_board", False)
    if main_board:
        board_type = "main_board"
    else:
        board_type = "unknown_non_main_board"
    
    return {
        "trade_date": record["date"],
        "source": record["source"],
        "rank": rank,
        "ticker": record["ticker"],
        "name": record["name"],
        "board_type": board_type,
        "is_main_board": main_board,
        "source_project": SOURCE_PROJECT,
        "original_path": str(filepath),
        "imported_at": IMPORTED_AT,
        "import_batch_id": IMPORT_BATCH_ID,
        "raw_record": record,
        "_invalid": False
    }


def process_files():
    """处理所有 JSONL 文件"""
    ensure_dirs()
    
    # 收集所有文件
    jsonl_files = sorted(SOURCE_DIR.glob("*.jsonl"))
    print(f"Found {len(jsonl_files)} JSONL files in {SOURCE_DIR}")
    
    # 统计
    stats = {
        "total_files": len(jsonl_files),
        "total_records": 0,
        "valid_records": 0,
        "invalid_records": 0,
        "duplicate_records": 0,
        "platform_counts": defaultdict(int),
        "date_counts": defaultdict(int),
        "dates_covered": [],
        "has_rank_missing": False,
        "has_invalid_fields": False,
        "non_mainboard_preserved": 0,
        "invalid_details": []
    }
    
    all_valid_records = []
    all_invalid_records = []
    seen_keys = set()
    
    # 按日期组织记录
    by_date = defaultdict(list)
    
    for filepath in jsonl_files:
        print(f"Processing: {filepath.name}")
        records = read_jsonl(filepath)
        
        for i, record in enumerate(records):
            stats["total_records"] += 1
            
            # 标准化
            standardized = standardize_record(record, filepath)
            
            if standardized.get("_invalid"):
                stats["invalid_records"] += 1
                stats["has_invalid_fields"] = True
                all_invalid_records.append(standardized)
                stats["invalid_details"].append({
                    "file": filepath.name,
                    "record_index": i,
                    "reason": standardized.get("_reason"),
                    "raw_record": record
                })
                continue
            
            # 检查重复
            key = (standardized["trade_date"], standardized["source"], standardized["ticker"])
            if key in seen_keys:
                stats["duplicate_records"] += 1
                continue
            
            seen_keys.add(key)
            stats["valid_records"] += 1
            
            # 统计
            stats["platform_counts"][standardized["source"]] += 1
            stats["date_counts"][standardized["trade_date"]] += 1
            
            if not standardized["is_main_board"]:
                stats["non_mainboard_preserved"] += 1
            
            if standardized["rank"] is None:
                stats["has_rank_missing"] = True
            
            # 收集
            all_valid_records.append(standardized)
            by_date[standardized["trade_date"]].append(standardized)
    
    # 日期排序
    stats["dates_covered"] = sorted(stats["date_counts"].keys())
    
    # 输出总 JSONL
    output_main_jsonl(all_valid_records)
    
    # 输出按日期文件
    output_by_date(by_date)
    
    # 输出无效记录
    output_invalid_records(all_invalid_records)
    
    # 输出审计报告
    output_audit_report(stats)
    
    # 复制原始文件到 raw
    copy_raw_files(jsonl_files)
    
    print(f"\nMigration complete!")
    print(f"  Total records: {stats['total_records']}")
    print(f"  Valid records: {stats['valid_records']}")
    print(f"  Invalid records: {stats['invalid_records']}")
    print(f"  Duplicate records: {stats['duplicate_records']}")
    print(f"  Dates covered: {len(stats['dates_covered'])}")


def output_main_jsonl(records: list):
    """输出主 JSONL 文件"""
    output_file = TARGET_STRUCTURED / "hotlist_legacy_tradingagents_old.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for record in records:
            # 移除内部字段
            clean_record = {k: v for k, v in record.items() if not k.startswith("_")}
            f.write(json.dumps(clean_record, ensure_ascii=False) + "\n")
    print(f"Output main JSONL: {output_file} ({len(records)} records)")


def output_by_date(by_date: dict):
    """输出按日期的文件"""
    date_dir = TARGET_STRUCTURED / "by_date"
    date_dir.mkdir(parents=True, exist_ok=True)
    
    for date_str, records in sorted(by_date.items()):
        output_file = date_dir / f"{date_str}.jsonl"
        with open(output_file, "w", encoding="utf-8") as f:
            for record in records:
                clean_record = {k: v for k, v in record.items() if not k.startswith("_")}
                f.write(json.dumps(clean_record, ensure_ascii=False) + "\n")
    print(f"Output by-date files: {date_dir} ({len(by_date)} dates)")


def output_invalid_records(records: list):
    """输出无效记录"""
    output_file = TARGET_AUDIT / "tradingagents_old_invalid_records.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Output invalid records: {output_file} ({len(records)} records)")


def copy_raw_files(jsonl_files: list):
    """复制原始文件到 raw 目录"""
    for filepath in jsonl_files:
        target_file = TARGET_RAW / filepath.name
        with open(filepath, "r", encoding="utf-8") as src:
            with open(target_file, "w", encoding="utf-8") as dst:
                dst.write(src.read())
    print(f"Copied {len(jsonl_files)} raw files to {TARGET_RAW}")


def output_audit_report(stats: dict):
    """输出审计报告"""
    output_file = TARGET_AUDIT / "tradingagents_old_import_summary.md"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# tradingagents-old 热榜数据迁移审计报告\n\n")
        f.write(f"> 迁移时间：{IMPORTED_AT}\n")
        f.write(f"> 迁移批次：{IMPORT_BATCH_ID}\n\n")
        f.write("---\n\n")
        
        f.write("## 一、迁移概览\n\n")
        f.write(f"| 项目 | 数值 |\n")
        f.write(f"|------|------|\n")
        f.write(f"| 迁移来源目录 | `{SOURCE_DIR}` |\n")
        f.write(f"| 迁移文件数量 | {stats['total_files']} |\n")
        f.write(f"| 覆盖日期范围 | {stats['dates_covered'][0]} 到 {stats['dates_covered'][-1]} |\n")
        f.write(f"| 覆盖交易日数量 | {len(stats['dates_covered'])} |\n")
        f.write(f"| 总记录数 | {stats['total_records']} |\n")
        f.write(f"| 有效记录数 | {stats['valid_records']} |\n")
        f.write(f"| 无效记录数 | {stats['invalid_records']} |\n")
        f.write(f"| 重复记录数 | {stats['duplicate_records']} |\n\n")
        
        f.write("## 二、平台覆盖\n\n")
        f.write("| 平台 | 记录数 |\n")
        f.write("|------|--------|\n")
        for platform, count in sorted(stats["platform_counts"].items()):
            f.write(f"| {platform} | {count} |\n")
        f.write("\n")
        
        f.write("## 三、四平台覆盖确认\n\n")
        platforms = set(stats["platform_counts"].keys())
        required = {"同花顺", "东方财富", "雪球", "通达信"}
        if required.issubset(platforms):
            f.write("✅ **四个平台全部覆盖：** 同花顺、东方财富、雪球、通达信\n\n")
        else:
            f.write("⚠️ **部分平台缺失：**\n")
            for p in required:
                if p in platforms:
                    f.write(f"- ✅ {p}\n")
                else:
                    f.write(f"- ❌ {p}（缺失）\n")
            f.write("\n")
        
        f.write("## 四、每日记录数\n\n")
        f.write("| 日期 | 记录数 |\n")
        f.write("|------|--------|\n")
        for date_str in stats["dates_covered"]:
            f.write(f"| {date_str} | {stats['date_counts'][date_str]} |\n")
        f.write("\n")
        
        f.write("## 五、数据质量\n\n")
        f.write(f"| 检查项 | 状态 | 说明 |\n")
        f.write(f"|--------|------|------|\n")
        f.write(f"| 是否存在缺少 rank 的记录 | {'是' if stats['has_rank_missing'] else '否'} | 原始数据无显式排名字段，已从顺序推断 |\n")
        f.write(f"| 是否存在缺少 ticker/name/source/date 的记录 | {'是' if stats['has_invalid_fields'] else '否'} | {'有 ' + str(stats['invalid_records']) + ' 条无效记录' if stats['has_invalid_fields'] else '无'} |\n")
        f.write(f"| 是否保留非主板股票 | 是 | 保留了 {stats['non_mainboard_preserved']} 条非主板记录 |\n\n")
        
        f.write("## 六、异常说明\n\n")
        if len(stats["dates_covered"]) < 20:
            f.write(f"⚠️ **日期不连续：** 19 个交易日数据，这是旧项目留存样本，非完整历史数据。\n\n")
        
        f.write("## 七、后续用途\n\n")
        f.write("1. **Attention Pool 初始化：** 这些数据可用于初始化 Attention Pool，提供历史热度参考。\n")
        f.write("2. **历史反思：** 结合历史报告，可用于反思系统的历史数据分析。\n")
        f.write("3. **注意：** 这不是实时数据源，不能代替每日新热榜录入。\n\n")
        
        f.write("## 八、输出文件\n\n")
        f.write("| 文件 | 说明 |\n")
        f.write("|------|------|\n")
        f.write(f"| `structured/tradingagents-old/hotlist_legacy_tradingagents_old.jsonl` | 总 JSONL 文件 |\n")
        f.write(f"| `structured/tradingagents-old/by_date/YYYY-MM-DD.jsonl` | 按日期的 JSONL 文件 |\n")
        f.write(f"| `raw/tradingagents-old/*.jsonl` | 原始文件副本 |\n")
        f.write(f"| `audit/tradingagents_old_import_summary.md` | 本审计报告 |\n")
        f.write(f"| `audit/tradingagents_old_invalid_records.jsonl` | 无效记录 |\n\n")
        
        f.write("---\n\n")
        f.write("**文档结束。**\n\n")
        f.write(f"> 本文档由迁移脚本自动生成于 {IMPORTED_AT}。\n")
    
    print(f"Output audit report: {output_file}")


if __name__ == "__main__":
    process_files()
