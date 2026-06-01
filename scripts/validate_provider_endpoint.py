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
    "tencent": {
        "valuation": {
            "url_template": "https://qt.gtimg.cn/q={symbol}",
            "method": "GET",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://finance.qq.com/",
            },
            "decode": "gbk",
            "symbol_format": {
                "sh_prefix": ["600", "601", "603", "605", "688", "689"],
                "sz_prefix": ["000", "001", "002", "003", "300", "301"],
            },
        },
        "market_cap": {
            "url_template": "https://qt.gtimg.cn/q={symbol}",
            "method": "GET",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://finance.qq.com/",
            },
            "decode": "gbk",
        },
        "turnover_rate": {
            "url_template": "https://qt.gtimg.cn/q={symbol}",
            "method": "GET",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://finance.qq.com/",
            },
            "decode": "gbk",
        },
        "limit_price": {
            "url_template": "https://qt.gtimg.cn/q={symbol}",
            "method": "GET",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://finance.qq.com/",
            },
            "decode": "gbk",
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

    # For Tencent endpoints
    if provider == "tencent" and dataset in ["valuation", "market_cap", "turnover_rate", "limit_price"]:
        return _validate_tencent_endpoint(
            symbol=symbol,
            dataset=dataset,
            config=config,
            timeout=timeout,
            raw_dir=raw_dir,
            verbose=verbose,
            headers=headers or {},
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


def _validate_tencent_endpoint(
    symbol: str,
    dataset: str,
    config: Dict[str, Any],
    timeout: int,
    raw_dir: Optional[Path],
    verbose: bool,
    headers: Dict[str, str],
    decode: str,
) -> Dict[str, Any]:
    """Validate Tencent Finance endpoint."""
    try:
        import requests
    except ImportError:
        return {
            "status": "error",
            "error": "requests library not installed",
        }

    # Build URL
    url_template = config.get("url_template", "")
    if not url_template:
        return {
            "status": "error",
            "error": "No URL template in config",
        }

    # Convert symbol to Tencent format (sh/sz prefix)
    tencent_symbol = _convert_to_tencent_symbol(symbol)
    url = url_template.format(symbol=tencent_symbol)

    # Merge headers
    request_headers = config.get("headers", {}).copy()
    request_headers.update(headers)

    # Get decode setting
    response_decode = decode if decode != "utf-8" else config.get("decode", "utf-8")

    if verbose:
        print(f"URL: {url}")
        print(f"Method: GET")
        print(f"Headers: {json.dumps(request_headers, indent=2)}")
        print(f"Decode: {response_decode}")

    try:
        response = requests.get(
            url,
            headers=request_headers,
            timeout=timeout,
        )

        # Decode response
        if response_decode == "auto":
            try:
                content = response.content.decode("gbk")
            except UnicodeDecodeError:
                try:
                    content = response.content.decode("gb2312")
                except UnicodeDecodeError:
                    content = response.content.decode("utf-8", errors="replace")
        else:
            content = response.content.decode(response_decode, errors="replace")

        result = {
            "status": "success" if response.status_code == 200 else "failed",
            "provider": "tencent",
            "dataset": dataset,
            "symbol": symbol,
            "tencent_symbol": tencent_symbol,
            "http_status": response.status_code,
            "content_type": response.headers.get("Content-Type", ""),
            "content_length": len(content),
            "is_text": True,
            "raw_content_preview": content[:500] if verbose else content[:300],
        }

        # Parse Tencent response format: v_sh600519="field1~field2~field3~..."
        if content and "=" in content:
            # Extract variable name and value
            var_part, _, value_part = content.partition("=")
            result["variable_name"] = var_part.strip()

            # Remove quotes
            value_part = value_part.strip().strip('"').strip(";").strip('"')

            if value_part:
                # Split by ~
                fields = value_part.split("~")
                result["field_count"] = len(fields)
                result["fields"] = fields

                # Known field positions (from public examples)
                # This is just a reference, actual positions may vary
                if len(fields) >= 45:
                    result["likely_fields"] = {
                        "name": fields[1] if len(fields) > 1 else None,
                        "code": fields[2] if len(fields) > 2 else None,
                        "current_price": fields[3] if len(fields) > 3 else None,
                        "yesterday_close": fields[4] if len(fields) > 4 else None,
                        "today_open": fields[5] if len(fields) > 5 else None,
                        "volume": fields[6] if len(fields) > 6 else None,
                        "outer_volume": fields[7] if len(fields) > 7 else None,
                        "inner_volume": fields[8] if len(fields) > 8 else None,
                        "buy1_price": fields[9] if len(fields) > 9 else None,
                        "buy1_volume": fields[10] if len(fields) > 10 else None,
                        "sell1_price": fields[19] if len(fields) > 19 else None,
                        "sell1_volume": fields[20] if len(fields) > 20 else None,
                        "timestamp": fields[30] if len(fields) > 30 else None,
                        "change_amount": fields[31] if len(fields) > 31 else None,
                        "change_percent": fields[32] if len(fields) > 32 else None,
                        "highest": fields[33] if len(fields) > 33 else None,
                        "lowest": fields[34] if len(fields) > 34 else None,
                        "price_volume_amount": fields[35] if len(fields) > 35 else None,
                        "volume_hand": fields[36] if len(fields) > 36 else None,
                        "amount_wan": fields[37] if len(fields) > 37 else None,
                        "turnover_rate": fields[38] if len(fields) > 38 else None,
                        "pe_ratio": fields[39] if len(fields) > 39 else None,
                        "amplitude": fields[43] if len(fields) > 43 else None,
                        "circulating_market_cap": fields[44] if len(fields) > 44 else None,
                        "total_market_cap": fields[45] if len(fields) > 45 else None,
                        "pb_ratio": fields[46] if len(fields) > 46 else None,
                        "limit_up_price": fields[47] if len(fields) > 47 else None,
                        "limit_down_price": fields[48] if len(fields) > 48 else None,
                    }
            else:
                result["fields"] = []
                result["field_count"] = 0
        else:
            result["fields"] = []
            result["field_count"] = 0

        # Save raw payload if requested
        if raw_dir:
            raw_path = Path(raw_dir) / f"tencent_{dataset}_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(content)
            result["raw_payload_path"] = str(raw_path)

        return result

    except requests.exceptions.Timeout:
        return {
            "status": "failed",
            "error": f"Request timeout after {timeout}s",
            "provider": "tencent",
            "dataset": dataset,
            "symbol": symbol,
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "status": "failed",
            "error": f"Connection error: {str(e)[:200]}",
            "provider": "tencent",
            "dataset": dataset,
            "symbol": symbol,
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": f"Unexpected error: {str(e)[:200]}",
            "provider": "tencent",
            "dataset": dataset,
            "symbol": symbol,
        }


def _convert_to_tencent_symbol(symbol: str) -> str:
    """Convert symbol to Tencent format (sh/sz prefix).

    Args:
        symbol: Stock symbol (e.g., "600519", "000001", "600519.SH")

    Returns:
        Tencent format symbol (e.g., "sh600519", "sz000001")
    """
    # Remove suffix if present
    if "." in symbol:
        symbol = symbol.split(".")[0]

    # Determine market
    if symbol.startswith(("600", "601", "603", "605", "688", "689")):
        return f"sh{symbol}"
    elif symbol.startswith(("000", "001", "002", "003", "300", "301")):
        return f"sz{symbol}"
    else:
        # Default to sh
        return f"sh{symbol}"


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
