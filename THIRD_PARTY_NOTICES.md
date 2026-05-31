# Third-Party Notices

This file documents third-party resources that this project references
or may reference in the future.

---

## a-stock-data

- **Repository:** https://github.com/simonlin1212/a-stock-data
- **License:** Apache License 2.0
- **Current Status:** Audited reference implementation, not vendored
- **Integration Policy:** Do not copy large code blocks without review; preserve attribution if code is reused

### Usage Notes

a-stock-data is an external reference implementation for A-stock data providers.
It provides:
- 7-layer architecture (market data, research, signals, capital flow, news, fundamentals, filings)
- 27 endpoints across 13 data sources
- Unified Eastmoney throttling via `em_get()`
- Data source priority: mootdx/Tencent first (no IP ban), Eastmoney last

### Attribution Requirements

If code from a-stock-data is reused in this project:
1. Preserve the Apache-2.0 license notice
2. Credit the original author (Simon Lin)
3. Document what was reused and where
4. Keep the original LICENSE file if vendoring

### Known Limitations

- Eastmoney APIs have rate limits (>5/s, ≥10 concurrent, ≥200/min, ≥300/5min)
- Financial news (cls.cn) has been deprecated, replaced by Eastmoney global news
- mootdx requires domestic China IP for TCP connections

---

**Last Updated:** 2026-05-31
