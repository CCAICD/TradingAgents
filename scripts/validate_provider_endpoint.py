"""Provider endpoint validation script.

This script validates provider endpoints before real implementation.
It is a research/smoke tool, NOT a formal provider.

Usage:
    python scripts/validate_provider_endpoint.py --provider mootdx --dataset daily_kline --symbol 600519.SH --allow-network

Safety:
    - Default offline (no network without --allow-network)
    - Max 5 requests per run
    - Raw payloads saved for audit
    - Not for production use
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def validate_provider_endpoint(
    provider: str,
    dataset: str,
    symbol: str,
    allow_network: bool = False,
    max_requests: int = 1,
    timeout: int = 10,
    raw_dir: Optional[Path] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Validate a provider endpoint.

    Args:
        provider: Provider name (mootdx, tencent, cninfo)
        dataset: Dataset name
        symbol: Stock symbol
        allow_network: Whether to allow network requests
        max_requests: Maximum number of requests (1-5)
        timeout: Request timeout in seconds
        raw_dir: Directory to save raw payloads
        verbose: Verbose output

    Returns:
        Dict with validation results
    """
    # Validate inputs
    if max_requests < 1 or max_requests > 5:
        return {
            "status": "error",
            "error": "max_requests must be between 1 and 5",
        }

    if not allow_network:
        return {
            "status": "skipped",
            "reason": "Network access not allowed. Use --allow-network to enable.",
            "provider": provider,
            "dataset": dataset,
            "symbol": symbol,
        }

    # This is where real validation would happen
    # For now, return a placeholder
    return {
        "status": "not_implemented",
        "reason": "Validation not yet implemented for this provider/dataset",
        "provider": provider,
        "dataset": dataset,
        "symbol": symbol,
        "note": "This is a validation harness, not a real provider",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate provider endpoints (research tool, not production)"
    )
    parser.add_argument(
        "--provider",
        type=str,
        required=True,
        choices=["mootdx", "tencent", "cninfo"],
        help="Provider name",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Dataset name",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        required=True,
        help="Stock symbol (e.g., 600519.SH)",
    )
    parser.add_argument(
        "--allow-network",
        action="store_true",
        default=False,
        help="Allow network requests",
    )
    parser.add_argument(
        "--max-requests",
        type=int,
        default=1,
        help="Maximum requests (1-5, default: 1)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)",
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=None,
        help="Directory to save raw payloads",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Verbose output",
    )

    args = parser.parse_args()

    raw_dir = Path(args.raw_dir) if args.raw_dir else None

    result = validate_provider_endpoint(
        provider=args.provider,
        dataset=args.dataset,
        symbol=args.symbol,
        allow_network=args.allow_network,
        max_requests=args.max_requests,
        timeout=args.timeout,
        raw_dir=raw_dir,
        verbose=args.verbose,
    )

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
