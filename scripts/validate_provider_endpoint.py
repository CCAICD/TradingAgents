"""Provider endpoint validation script.

This script validates provider endpoints before real implementation.
It is a research/smoke tool, NOT a formal provider.

Usage:
    python scripts/validate_provider_endpoint.py --provider cninfo --dataset announcement --symbol 000001 --allow-network --method POST --form "stock=000001" --form "pageSize=5"

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

# Known endpoint configurations
ENDPOINT_CONFIGS = {
    "cninfo": {
        "announcement": {
            "url": "http://www.cninfo.com.cn/new/hisAnnouncement/query",
            "method": "POST",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
                "Origin": "http://www.cninfo.com.cn",
            },
            "default_form": {
                "pageNum": "1",
                "pageSize": "5",
                "tabName": "fulltext",
                "column": "szse",
            },
        },
    },
}


def validate_provider_endpoint(
    provider: str,
    dataset: str,
    symbol: str,
    allow_network: bool = False,
    max_requests: int = 1,
    timeout: int = 10,
    raw_dir: Optional[Path] = None,
    verbose: bool = False,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    form_data: Optional[Dict[str, str]] = None,
    decode: str = "utf-8",
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
        method: HTTP method (GET/POST)
        headers: Custom headers
        form_data: Form data for POST requests
        decode: Response decoding (utf-8/gbk/auto)

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

    # Get endpoint config if available
    config = ENDPOINT_CONFIGS.get(provider, {}).get(dataset, {})

    if not config:
        return {
            "status": "not_implemented",
            "reason": f"No endpoint configuration for {provider}/{dataset}",
            "provider": provider,
            "dataset": dataset,
            "symbol": symbol,
        }

    # For Cninfo announcement endpoint
    if provider == "cninfo" and dataset == "announcement":
        return _validate_cninfo_announcement(
            symbol=symbol,
            config=config,
            max_requests=max_requests,
            timeout=timeout,
            raw_dir=raw_dir,
            verbose=verbose,
            headers=headers or {},
            form_data=form_data or {},
            decode=decode,
        )

    return {
        "status": "not_implemented",
        "reason": f"Validation not implemented for {provider}/{dataset}",
        "provider": provider,
        "dataset": dataset,
        "symbol": symbol,
    }


def _validate_cninfo_announcement(
    symbol: str,
    config: Dict[str, Any],
    max_requests: int,
    timeout: int,
    raw_dir: Optional[Path],
    verbose: bool,
    headers: Dict[str, str],
    form_data: Dict[str, str],
    decode: str,
) -> Dict[str, Any]:
    """Validate Cninfo announcement endpoint."""
    try:
        import requests
    except ImportError:
        return {
            "status": "error",
            "error": "requests library not installed",
        }

    # Merge headers
    request_headers = config.get("headers", {}).copy()
    request_headers.update(headers)

    # Merge form data
    request_form = config.get("default_form", {}).copy()
    request_form["stock"] = symbol
    request_form.update(form_data)

    url = config["url"]

    if verbose:
        print(f"URL: {url}")
        print(f"Method: POST")
        print(f"Headers: {json.dumps(request_headers, indent=2)}")
        print(f"Form: {json.dumps(request_form, indent=2)}")

    try:
        response = requests.post(
            url,
            data=request_form,
            headers=request_headers,
            timeout=timeout,
        )

        # Try to decode response
        if decode == "auto":
            try:
                content = response.text
            except Exception:
                content = response.content.decode("utf-8", errors="replace")
        else:
            content = response.content.decode(decode, errors="replace")

        result = {
            "status": "success" if response.status_code == 200 else "failed",
            "provider": "cninfo",
            "dataset": "announcement",
            "symbol": symbol,
            "http_status": response.status_code,
            "content_type": response.headers.get("Content-Type", ""),
            "content_length": len(content),
            "is_json": False,
            "fields_found": [],
            "raw_content_preview": content[:1000] if verbose else content[:200],
        }

        # Try to parse as JSON
        try:
            data = response.json()
            result["is_json"] = True
            result["json_keys"] = list(data.keys()) if isinstance(data, dict) else []

            # Check for announcements array
            if isinstance(data, dict) and "announcements" in data:
                result["has_announcements"] = True
                result["announcement_count"] = len(data["announcements"])
                if data["announcements"]:
                    result["fields_found"] = list(data["announcements"][0].keys())
            else:
                result["has_announcements"] = False

            result["raw_json"] = data
        except Exception:
            result["has_announcements"] = False

        # Save raw payload if requested
        if raw_dir:
            raw_path = Path(raw_dir) / f"cninfo_announcement_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            result["raw_payload_path"] = str(raw_path)

        return result

    except requests.exceptions.Timeout:
        return {
            "status": "failed",
            "error": f"Request timeout after {timeout}s",
            "provider": "cninfo",
            "dataset": "announcement",
            "symbol": symbol,
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "status": "failed",
            "error": f"Connection error: {str(e)[:200]}",
            "provider": "cninfo",
            "dataset": "announcement",
            "symbol": symbol,
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": f"Unexpected error: {str(e)[:200]}",
            "provider": "cninfo",
            "dataset": "announcement",
            "symbol": symbol,
        }


def main():
    parser = argparse.ArgumentParser(
        description="Validate provider endpoints (research tool, not production)"
    )
    parser.add_argument("--provider", type=str, required=True, choices=["mootdx", "tencent", "cninfo"])
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--symbol", type=str, required=True)
    parser.add_argument("--allow-network", action="store_true", default=False)
    parser.add_argument("--max-requests", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--raw-dir", type=str, default=None)
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument("--method", type=str, default="GET", choices=["GET", "POST"])
    parser.add_argument("--header", action="append", default=[], help="Header in format 'Key: Value'")
    parser.add_argument("--form", action="append", default=[], help="Form data in format 'key=value'")
    parser.add_argument("--decode", type=str, default="utf-8", choices=["utf-8", "gbk", "auto"])

    args = parser.parse_args()

    # Parse headers
    headers = {}
    for h in args.header:
        if ":" in h:
            key, value = h.split(":", 1)
            headers[key.strip()] = value.strip()

    # Parse form data
    form_data = {}
    for f in args.form:
        if "=" in f:
            key, value = f.split("=", 1)
            form_data[key.strip()] = value.strip()

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
        method=args.method,
        headers=headers,
        form_data=form_data,
        decode=args.decode,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
