"""Smoke test script for MootdxProvider.

This script is for manual testing only. It requires:
1. mootdx installed: pip install mootdx
2. Domestic China IP for TCP connections
3. Explicit --allow-network flag

Usage:
    python scripts/smoke_test_mootdx_provider.py --allow-network
    python scripts/smoke_test_mootdx_provider.py --allow-network --symbol 600519.SH
    python scripts/smoke_test_mootdx_provider.py --allow-network --dataset daily_kline
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(
        description="Smoke test for MootdxProvider (requires --allow-network)"
    )
    parser.add_argument(
        "--allow-network",
        action="store_true",
        default=False,
        help="Allow network calls to mootdx servers",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="600519.SH",
        help="Stock symbol to test (default: 600519.SH)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        choices=[
            "daily_kline",
            "minute_kline",
            "index_kline",
            "realtime_quote",
            "order_book",
            "all",
        ],
        default="all",
        help="Dataset to test (default: all)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of records to fetch (default: 10)",
    )

    args = parser.parse_args()

    if not args.allow_network:
        print("=" * 60)
        print("ERROR: Network access not allowed.")
        print()
        print("This script requires --allow-network flag because it")
        print("makes real network calls to mootdx (通达信) servers.")
        print()
        print("Usage:")
        print("  python scripts/smoke_test_mootdx_provider.py --allow-network")
        print("=" * 60)
        sys.exit(1)

    # Import after argument parsing to avoid import errors
    try:
        from tradingagents.markets.cn_stock.data_providers.mootdx_provider import (
            MootdxProvider,
        )
        from tradingagents.markets.cn_stock.data_providers.schema import ProviderStatus
    except ImportError as e:
        print(f"ERROR: Failed to import tradingagents modules: {e}")
        print("Make sure you're running from the project root directory.")
        sys.exit(1)

    # Check mootdx availability
    try:
        import mootdx  # noqa: F401
        print(f"mootdx version: {mootdx.__version__}")
    except ImportError:
        print("ERROR: mootdx is not installed.")
        print("Install with: pip install mootdx")
        sys.exit(1)

    provider = MootdxProvider()

    print("=" * 60)
    print("MootdxProvider Smoke Test")
    print("=" * 60)
    print(f"Symbol: {args.symbol}")
    print(f"Dataset: {args.dataset}")
    print(f"Count: {args.count}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)

    datasets_to_test = []
    if args.dataset == "all":
        datasets_to_test = [
            "daily_kline",
            "minute_kline",
            "index_kline",
            "realtime_quote",
            "order_book",
        ]
    else:
        datasets_to_test = [args.dataset]

    results_summary = []

    for dataset in datasets_to_test:
        print(f"\n--- Testing {dataset} ---")

        kwargs = {"symbol": args.symbol, "count": args.count}
        if dataset == "index_kline":
            # Use index symbol
            kwargs["symbol"] = "000001"  # Shanghai Composite Index

        try:
            result = provider.fetch_and_normalize(dataset, **kwargs)

            status_icon = "OK" if result.status == ProviderStatus.SUCCESS else "FAIL"
            print(f"  Status: {status_icon} {result.status.value}")
            print(f"  Fetched at: {result.fetched_at}")
            print(f"  As of time: {result.as_of_time}")

            if result.error_message:
                print(f"  Error: {result.error_message}")

            if result.warnings:
                print(f"  Warnings:")
                for w in result.warnings:
                    print(f"    - {w}")

            if result.raw_payload_path:
                print(f"  Raw payload: {result.raw_payload_path}")

            if result.metadata:
                print(f"  Metadata: {json.dumps(result.metadata, indent=2)}")

            # Show data preview
            data = result.normalized_data or result.data
            if data:
                if isinstance(data, list):
                    print(f"  Data records: {len(data)}")
                    if data:
                        print(f"  First record keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'N/A'}")
                elif isinstance(data, dict):
                    print(f"  Data keys: {list(data.keys())}")

            results_summary.append({
                "dataset": dataset,
                "status": result.status.value,
                "has_data": data is not None,
                "error": result.error_message,
            })

        except Exception as e:
            print(f"  EXCEPTION: {e}")
            results_summary.append({
                "dataset": dataset,
                "status": "exception",
                "has_data": False,
                "error": str(e),
            })

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for r in results_summary:
        icon = "OK" if r["status"] == "success" else "FAIL"
        print(f"  {icon} {r['dataset']}: {r['status']}")
        if r["error"]:
            print(f"    Error: {r['error']}")

    print("\nSmoke test completed.")


if __name__ == "__main__":
    main()
