"""mootdx data provider for A-stock market data.

This provider uses the mootdx library to fetch:
- daily_kline: Daily K-line data
- minute_kline: Minute K-line data
- index_kline: Index K-line data
- realtime_quote: Real-time quote with five-level order book
- order_book: Extracted order book from quote data

NOTE: mootdx requires domestic China IP for TCP connections to TDX servers.

Limitations:
- finance and F10 are planned for later phase
- tick data is not implemented
- order_book depends on mootdx quote response containing bid/ask fields
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .base import BaseCnStockProvider
from .raw_store import RawPayloadStore
from .rate_limiter import ProviderRateLimitConfig, get_provider_limiter
from .schema import ProviderResult, ProviderStatus

logger = logging.getLogger(__name__)

# Market constants for mootdx
MARKET_SH = 1  # Shanghai
MARKET_SZ = 0  # Shenzhen
MARKET_BJ = 2  # Beijing (not well supported by mootdx)

# Symbol prefix to market mapping
_PREFIX_MARKET_MAP = {
    "600": MARKET_SH,
    "601": MARKET_SH,
    "603": MARKET_SH,
    "605": MARKET_SH,
    "688": MARKET_SH,  # STAR Market
    "689": MARKET_SH,  # STAR Market CDR
    "000": MARKET_SZ,
    "001": MARKET_SZ,
    "002": MARKET_SZ,
    "003": MARKET_SZ,
    "300": MARKET_SZ,  # ChiNext
    "301": MARKET_SZ,  # ChiNext
}

# Kline frequency mapping
_FREQ_MAP = {
    "day": 9,
    "week": 5,
    "month": 6,
    "1min": 8,
    "5min": 0,
    "15min": 1,
    "30min": 2,
    "60min": 3,
}


class MootdxProvider(BaseCnStockProvider):
    """Provider for A-stock data via mootdx (通达信).

    mootdx is a Python library for accessing 通达信 (TDX) stock data servers.
    It provides real-time quotes, K-line data, and other market data.

    Requires:
    - mootdx package installed
    - Domestic China IP for TCP connections
    """

    def __init__(
        self,
        raw_store: Optional[RawPayloadStore] = None,
        rate_limit_config: Optional[ProviderRateLimitConfig] = None,
    ):
        """Initialize MootdxProvider.

        Args:
            raw_store: RawPayloadStore for saving raw payloads
            rate_limit_config: Rate limit configuration
        """
        self._raw_store = raw_store or RawPayloadStore()
        self._rate_limit_config = rate_limit_config or ProviderRateLimitConfig(
            min_interval_seconds=0.2,
            jitter_seconds=0.05,
        )
        # Create a new RateLimiter with the desired config
        from .rate_limiter import RateLimiter
        self._limiter = RateLimiter(config=self._rate_limit_config)
        self._quotes_client = None

    @property
    def provider_name(self) -> str:
        return "mootdx"

    @property
    def supported_datasets(self) -> List[str]:
        return [
            "daily_kline",
            "minute_kline",
            "index_kline",
            "realtime_quote",
            "order_book",
        ]

    def _check_mootdx_available(self) -> Optional[str]:
        """Check if mootdx is available.

        Returns:
            Error message if not available, None if available
        """
        try:
            import mootdx  # noqa: F401
            return None
        except ImportError:
            return "mootdx is not installed. Install with: pip install mootdx"

    def _get_quotes_client(self):
        """Get or create mootdx Quotes client (lazy initialization).

        Returns:
            Tuple of (client, error_message). client is None if error.
        """
        if self._quotes_client is not None:
            return self._quotes_client, None

        error = self._check_mootdx_available()
        if error:
            return None, error

        try:
            from mootdx.quotes import Quotes

            # Use default server (best server auto-detected)
            self._quotes_client = Quotes.factory(market="std")
            return self._quotes_client, None
        except Exception as e:
            return None, f"Failed to initialize mootdx Quotes client: {e}"

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol by removing exchange suffix.

        Args:
            symbol: Stock symbol, e.g., '600519', '600519.SH'

        Returns:
            Clean symbol without suffix
        """
        symbol = symbol.strip().upper()
        if "." in symbol:
            symbol = symbol.split(".")[0]
        return symbol

    def _infer_market_from_symbol(self, symbol: str) -> tuple:
        """Infer market from symbol.

        Args:
            symbol: Stock symbol (without suffix)

        Returns:
            Tuple of (market_id, warning_message)
            market_id: MARKET_SH, MARKET_SZ, or -1 for unknown
        """
        # Check suffix first
        if "." in symbol:
            suffix = symbol.split(".")[-1].upper()
            if suffix == "SH":
                return MARKET_SH, None
            elif suffix == "SZ":
                return MARKET_SZ, None

        # Clean symbol
        clean = self._normalize_symbol(symbol)

        # Check prefix
        for prefix, market in _PREFIX_MARKET_MAP.items():
            if clean.startswith(prefix):
                return market, None

        # Check Beijing Exchange
        if clean.startswith("8") or clean.startswith("4"):
            return MARKET_BJ, f"Beijing Exchange symbol {symbol} may not be fully supported by mootdx"

        return -1, f"Cannot infer market from symbol: {symbol}"

    def _normalize_dataframe_or_records(self, raw_data: Any) -> Any:
        """Normalize mootdx DataFrame or list to JSON-serializable format.

        Args:
            raw_data: Raw data from mootdx (DataFrame or list)

        Returns:
            Normalized data (list of dicts or dict)
        """
        if raw_data is None:
            return None

        # If it's a pandas DataFrame, convert to list of dicts
        try:
            import pandas as pd

            if isinstance(raw_data, pd.DataFrame):
                if raw_data.empty:
                    return []
                # Convert to records, handling datetime columns
                records = raw_data.to_dict(orient="records")
                # Convert datetime objects to ISO strings
                for record in records:
                    for key, value in record.items():
                        if isinstance(value, datetime):
                            record[key] = value.isoformat()
                        elif hasattr(value, "isoformat"):
                            record[key] = value.isoformat()
                return records
        except ImportError:
            pass

        # If it's already a list, try to convert each item
        if isinstance(raw_data, list):
            result = []
            for item in raw_data:
                if isinstance(item, dict):
                    # Convert datetime objects
                    converted = {}
                    for key, value in item.items():
                        if isinstance(value, datetime):
                            converted[key] = value.isoformat()
                        elif hasattr(value, "isoformat"):
                            converted[key] = value.isoformat()
                        else:
                            converted[key] = value
                    result.append(converted)
                else:
                    result.append(item)
            return result

        # If it's a dict, return as is
        if isinstance(raw_data, dict):
            return raw_data

        return raw_data

    def _extract_as_of_time(
        self, normalized_data: Any, fallback_now: datetime
    ) -> tuple:
        """Extract as_of_time from normalized data.

        Args:
            normalized_data: Normalized data
            fallback_now: Fallback time if extraction fails

        Returns:
            Tuple of (as_of_time, warning_message)
        """
        if normalized_data is None:
            return fallback_now, "No data, using current time as as_of_time"

        # Try to extract from data
        if isinstance(normalized_data, list) and len(normalized_data) > 0:
            last_record = normalized_data[-1]
            if isinstance(last_record, dict):
                # Try common time fields
                for field in ["datetime", "date", "time", "trade_date"]:
                    if field in last_record:
                        try:
                            val = last_record[field]
                            if isinstance(val, str):
                                # Try common formats
                                for fmt in [
                                    "%Y-%m-%d %H:%M:%S",
                                    "%Y-%m-%d",
                                    "%Y%m%d",
                                    "%Y-%m-%d %H:%M",
                                ]:
                                    try:
                                        return datetime.strptime(val, fmt), None
                                    except ValueError:
                                        continue
                        except Exception:
                            pass

        # Fallback
        return fallback_now, "Cannot extract as_of_time from data, using fetched_at"

    def fetch(self, dataset_name: str, **kwargs) -> ProviderResult:
        """Fetch data from mootdx.

        Args:
            dataset_name: Name of the dataset to fetch
            **kwargs: Additional parameters

        Returns:
            ProviderResult with fetched data
        """
        now = datetime.now()

        # Check mootdx availability
        error = self._check_mootdx_available()
        if error:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name=dataset_name,
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=error,
            )

        # Rate limiting
        self._limiter.wait()

        # Dispatch to specific fetch methods
        try:
            if dataset_name == "daily_kline":
                result = self._fetch_daily_kline(now, **kwargs)
            elif dataset_name == "minute_kline":
                result = self._fetch_minute_kline(now, **kwargs)
            elif dataset_name == "index_kline":
                result = self._fetch_index_kline(now, **kwargs)
            elif dataset_name == "realtime_quote":
                result = self._fetch_realtime_quote(now, **kwargs)
            elif dataset_name == "order_book":
                result = self._fetch_order_book(now, **kwargs)
            else:
                result = ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name=dataset_name,
                    status=ProviderStatus.FAILED,
                    fetched_at=now,
                    error_message=f"Unsupported dataset: {dataset_name}",
                )

            # Record call for rate limiting
            self._limiter.record_call()
            return result

        except Exception as e:
            logger.error(f"mootdx fetch failed for {dataset_name}: {e}")
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name=dataset_name,
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"Fetch failed: {e}",
            )

    def _fetch_daily_kline(self, now: datetime, **kwargs) -> ProviderResult:
        """Fetch daily K-line data."""
        symbol = kwargs.get("symbol")
        if not symbol:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="daily_kline",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message="symbol is required for daily_kline",
            )

        frequency = kwargs.get("frequency", "day")
        offset = kwargs.get("offset", 0)
        count = kwargs.get("count", 100)

        client, error = self._get_quotes_client()
        if error:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="daily_kline",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=error,
            )

        clean_symbol = self._normalize_symbol(symbol)
        market, market_warning = self._infer_market_from_symbol(symbol)

        if market == -1:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="daily_kline",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"Cannot determine market for symbol: {symbol}",
            )

        freq_code = _FREQ_MAP.get(frequency, 9)

        try:
            # mootdx bars method: bars(category, market, symbol, start, offset)
            # category: 9=day, 5=week, 6=month, 8=1min, 0=5min, 1=15min, 2=30min, 3=60min
            raw_data = client.bars(
                category=freq_code,
                market=market,
                symbol=clean_symbol,
                start=offset,
                offset=count,
            )

            if raw_data is None or (hasattr(raw_data, "empty") and raw_data.empty):
                return ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name="daily_kline",
                    source="mootdx",
                    status=ProviderStatus.EMPTY,
                    fetched_at=now,
                    error_message=f"No data returned for {symbol}",
                    metadata={
                        "symbol": clean_symbol,
                        "market": market,
                        "frequency": frequency,
                    },
                )

            normalized = self._normalize_dataframe_or_records(raw_data)
            as_of_time, time_warning = self._extract_as_of_time(normalized, now)

            # Save raw payload
            raw_path = self._raw_store.save(
                provider_name=self.provider_name,
                dataset_name="daily_kline",
                data=raw_data,
                symbol=clean_symbol,
                file_format="json" if isinstance(raw_data, (dict, list)) else "text",
            )

            warnings = []
            if market_warning:
                warnings.append(market_warning)
            if time_warning:
                warnings.append(time_warning)

            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="daily_kline",
                source="mootdx",
                status=ProviderStatus.SUCCESS,
                fetched_at=now,
                as_of_time=as_of_time,
                data=raw_data,
                normalized_data=normalized,
                raw_payload_path=str(raw_path),
                warnings=warnings,
                metadata={
                    "symbol": clean_symbol,
                    "market": market,
                    "frequency": frequency,
                    "offset": offset,
                    "count": count,
                },
            )

        except Exception as e:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="daily_kline",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"mootdx bars failed: {e}",
            )

    def _fetch_minute_kline(self, now: datetime, **kwargs) -> ProviderResult:
        """Fetch minute K-line data."""
        symbol = kwargs.get("symbol")
        if not symbol:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="minute_kline",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message="symbol is required for minute_kline",
            )

        frequency = kwargs.get("frequency", "1min")
        offset = kwargs.get("offset", 0)
        count = kwargs.get("count", 100)

        client, error = self._get_quotes_client()
        if error:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="minute_kline",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=error,
            )

        clean_symbol = self._normalize_symbol(symbol)
        market, market_warning = self._infer_market_from_symbol(symbol)

        if market == -1:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="minute_kline",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"Cannot determine market for symbol: {symbol}",
            )

        freq_code = _FREQ_MAP.get(frequency, 8)

        try:
            raw_data = client.bars(
                category=freq_code,
                market=market,
                symbol=clean_symbol,
                start=offset,
                offset=count,
            )

            if raw_data is None or (hasattr(raw_data, "empty") and raw_data.empty):
                return ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name="minute_kline",
                    source="mootdx",
                    status=ProviderStatus.EMPTY,
                    fetched_at=now,
                    error_message=f"No data returned for {symbol}",
                    metadata={
                        "symbol": clean_symbol,
                        "market": market,
                        "frequency": frequency,
                    },
                )

            normalized = self._normalize_dataframe_or_records(raw_data)
            as_of_time, time_warning = self._extract_as_of_time(normalized, now)

            raw_path = self._raw_store.save(
                provider_name=self.provider_name,
                dataset_name="minute_kline",
                data=raw_data,
                symbol=clean_symbol,
                file_format="json" if isinstance(raw_data, (dict, list)) else "text",
            )

            warnings = []
            if market_warning:
                warnings.append(market_warning)
            if time_warning:
                warnings.append(time_warning)

            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="minute_kline",
                source="mootdx",
                status=ProviderStatus.SUCCESS,
                fetched_at=now,
                as_of_time=as_of_time,
                data=raw_data,
                normalized_data=normalized,
                raw_payload_path=str(raw_path),
                warnings=warnings,
                metadata={
                    "symbol": clean_symbol,
                    "market": market,
                    "frequency": frequency,
                    "offset": offset,
                    "count": count,
                },
            )

        except Exception as e:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="minute_kline",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"mootdx bars failed: {e}",
            )

    def _fetch_index_kline(self, now: datetime, **kwargs) -> ProviderResult:
        """Fetch index K-line data.

        Index symbols:
        - 000001: Shanghai Composite Index (market=1)
        - 399001: Shenzhen Component Index (market=0)
        - 399006: ChiNext Index (market=0)
        - 000688: STAR 50 Index (market=1)
        """
        symbol = kwargs.get("symbol")
        if not symbol:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="index_kline",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message="symbol is required for index_kline",
            )

        frequency = kwargs.get("frequency", "day")
        offset = kwargs.get("offset", 0)
        count = kwargs.get("count", 100)

        client, error = self._get_quotes_client()
        if error:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="index_kline",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=error,
            )

        clean_symbol = self._normalize_symbol(symbol)

        # Index market inference
        market = kwargs.get("market")
        if market is None:
            if clean_symbol.startswith("000") or clean_symbol.startswith("880"):
                market = MARKET_SH
            elif clean_symbol.startswith("399"):
                market = MARKET_SZ
            else:
                market = MARKET_SH  # Default to Shanghai
                logger.warning(f"Cannot infer index market for {symbol}, defaulting to Shanghai")

        freq_code = _FREQ_MAP.get(frequency, 9)

        try:
            # Use index_bars for index data
            raw_data = client.index_bars(
                category=freq_code,
                market=market,
                symbol=clean_symbol,
                start=offset,
                offset=count,
            )

            if raw_data is None or (hasattr(raw_data, "empty") and raw_data.empty):
                return ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name="index_kline",
                    source="mootdx",
                    status=ProviderStatus.EMPTY,
                    fetched_at=now,
                    error_message=f"No data returned for index {symbol}",
                    metadata={
                        "symbol": clean_symbol,
                        "market": market,
                        "frequency": frequency,
                    },
                )

            normalized = self._normalize_dataframe_or_records(raw_data)
            as_of_time, time_warning = self._extract_as_of_time(normalized, now)

            raw_path = self._raw_store.save(
                provider_name=self.provider_name,
                dataset_name="index_kline",
                data=raw_data,
                symbol=clean_symbol,
                file_format="json" if isinstance(raw_data, (dict, list)) else "text",
            )

            warnings = []
            if time_warning:
                warnings.append(time_warning)

            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="index_kline",
                source="mootdx",
                status=ProviderStatus.SUCCESS,
                fetched_at=now,
                as_of_time=as_of_time,
                data=raw_data,
                normalized_data=normalized,
                raw_payload_path=str(raw_path),
                warnings=warnings,
                metadata={
                    "symbol": clean_symbol,
                    "market": market,
                    "frequency": frequency,
                    "offset": offset,
                    "count": count,
                },
            )

        except Exception as e:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="index_kline",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"mootdx index_bars failed: {e}",
            )

    def _fetch_realtime_quote(self, now: datetime, **kwargs) -> ProviderResult:
        """Fetch real-time quote data.

        Args:
            symbols: List of symbols or single symbol
        """
        symbols = kwargs.get("symbols") or kwargs.get("symbol")
        if not symbols:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="realtime_quote",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message="symbols is required for realtime_quote",
            )

        # Normalize to list
        if isinstance(symbols, str):
            symbols = [symbols]

        client, error = self._get_quotes_client()
        if error:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="realtime_quote",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=error,
            )

        try:
            # mootdx quotes method accepts list of symbols
            # Need to pass market and symbol separately
            symbols_data = []
            for sym in symbols:
                clean = self._normalize_symbol(sym)
                market, warning = self._infer_market_from_symbol(sym)
                if market == -1:
                    logger.warning(f"Skipping symbol {sym}: cannot determine market")
                    continue
                symbols_data.append((market, clean))

            if not symbols_data:
                return ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name="realtime_quote",
                    status=ProviderStatus.EMPTY,
                    fetched_at=now,
                    error_message="No valid symbols to query",
                )

            # mootdx quotes: quotes(market, symbol_list)
            # For single symbol, use quote() method
            results = []
            for market, sym in symbols_data:
                try:
                    raw = client.quotes(market=market, symbol=sym)
                    if raw is not None and not (hasattr(raw, "empty") and raw.empty):
                        normalized = self._normalize_dataframe_or_records(raw)
                        results.extend(normalized if isinstance(normalized, list) else [normalized])
                except Exception as e:
                    logger.warning(f"Failed to fetch quote for {sym}: {e}")

            if not results:
                return ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name="realtime_quote",
                    source="mootdx",
                    status=ProviderStatus.EMPTY,
                    fetched_at=now,
                    error_message=f"No quote data returned for symbols: {symbols}",
                    metadata={"symbols": [self._normalize_symbol(s) for s in symbols]},
                )

            raw_path = self._raw_store.save(
                provider_name=self.provider_name,
                dataset_name="realtime_quote",
                data=results,
                file_format="json",
            )

            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="realtime_quote",
                source="mootdx",
                status=ProviderStatus.SUCCESS,
                fetched_at=now,
                as_of_time=now,  # Real-time data
                data=results,
                normalized_data=results,
                raw_payload_path=str(raw_path),
                metadata={
                    "symbols": [self._normalize_symbol(s) for s in symbols],
                    "count": len(results),
                },
            )

        except Exception as e:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="realtime_quote",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"mootdx quotes failed: {e}",
            )

    def _fetch_order_book(self, now: datetime, **kwargs) -> ProviderResult:
        """Fetch order book data from quote.

        mootdx quote response contains bid1-bid5 and ask1-ask5 fields.
        If not available, returns partial status.
        """
        symbols = kwargs.get("symbols") or kwargs.get("symbol")
        if not symbols:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="order_book",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message="symbols is required for order_book",
            )

        # Normalize to list
        if isinstance(symbols, str):
            symbols = [symbols]

        client, error = self._get_quotes_client()
        if error:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="order_book",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=error,
            )

        try:
            results = []
            has_order_book = False

            for sym in symbols:
                clean = self._normalize_symbol(sym)
                market, warning = self._infer_market_from_symbol(sym)
                if market == -1:
                    logger.warning(f"Skipping symbol {sym}: cannot determine market")
                    continue

                try:
                    raw = client.quotes(market=market, symbol=clean)
                    if raw is not None and not (hasattr(raw, "empty") and raw.empty):
                        normalized = self._normalize_dataframe_or_records(raw)
                        if isinstance(normalized, list):
                            for record in normalized:
                                # Check for bid/ask fields
                                if isinstance(record, dict):
                                    bid_fields = [f for f in record.keys() if f.startswith("bid")]
                                    ask_fields = [f for f in record.keys() if f.startswith("ask")]
                                    if bid_fields or ask_fields:
                                        has_order_book = True
                                    record["_symbol"] = clean
                                    record["_market"] = market
                                    results.append(record)
                        elif isinstance(normalized, dict):
                            bid_fields = [f for f in normalized.keys() if f.startswith("bid")]
                            ask_fields = [f for f in normalized.keys() if f.startswith("ask")]
                            if bid_fields or ask_fields:
                                has_order_book = True
                            normalized["_symbol"] = clean
                            normalized["_market"] = market
                            results.append(normalized)
                except Exception as e:
                    logger.warning(f"Failed to fetch order book for {sym}: {e}")

            if not results:
                return ProviderResult(
                    provider_name=self.provider_name,
                    dataset_name="order_book",
                    source="mootdx",
                    status=ProviderStatus.EMPTY,
                    fetched_at=now,
                    error_message=f"No order book data returned for symbols: {symbols}",
                    metadata={"symbols": [self._normalize_symbol(s) for s in symbols]},
                )

            raw_path = self._raw_store.save(
                provider_name=self.provider_name,
                dataset_name="order_book",
                data=results,
                file_format="json",
            )

            warnings = []
            status = ProviderStatus.SUCCESS
            if not has_order_book:
                status = ProviderStatus.PARTIAL
                warnings.append(
                    "Order book (bid/ask) fields not found in mootdx response. "
                    "Returning raw quote data as partial result."
                )

            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="order_book",
                source="mootdx",
                status=status,
                fetched_at=now,
                as_of_time=now,
                data=results,
                normalized_data=results,
                raw_payload_path=str(raw_path),
                warnings=warnings,
                metadata={
                    "symbols": [self._normalize_symbol(s) for s in symbols],
                    "count": len(results),
                    "has_order_book": has_order_book,
                },
            )

        except Exception as e:
            return ProviderResult(
                provider_name=self.provider_name,
                dataset_name="order_book",
                status=ProviderStatus.FAILED,
                fetched_at=now,
                error_message=f"mootdx order_book failed: {e}",
            )
