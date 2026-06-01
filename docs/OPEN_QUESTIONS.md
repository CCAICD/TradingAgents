# Open Questions

## For User/ChatGPT Confirmation

### 1. mootdx Dependency Lock File
**Question:** Does the project have uv.lock, poetry.lock, or requirements lock file that needs updating after adding mootdx to pyproject.toml?
**Status:** Pending confirmation
**Impact:** May need to run lock file update command

### 2. mootdx Server Availability
**Question:** Is mootdx TCP connection to TDX servers reliable from user's network environment?
**Status:** Smoke test failed (2026-06-01)
**Result:** `head_buf is not 0x10 : b''` - TDX server connection failed
**Impact:** Affects reliability of real-time data
**Next:** Retry with different network environment or available TDX server nodes

### 3. Beijing Exchange Support
**Question:** Does mootdx support Beijing Exchange (北交所) symbols?
**Status:** Pending smoke test
**Impact:** May need special handling for 8xx/4xx symbols

### 4. Tencent Batch Query Support
**Question:** Does Tencent Finance API support batch queries (multiple symbols in one request)?
**Status:** Unverified
**Impact:** Could improve efficiency for multi-stock queries

### 5. Tencent Unit Confirmation
**Question:** What are the exact units for Tencent market_cap fields?
**Status:** Likely 亿元 (100 million yuan) but unverified
**Impact:** May need unit conversion for consistency

### 6. Tencent Beijing Exchange Support
**Question:** Does Tencent Finance API support Beijing Exchange (北交所) symbols?
**Status:** Unverified, warning added for 8xx/4xx symbols
**Impact:** May need special handling

### 7. Cninfo Endpoint Long-Term Stability
**Question:** Is Cninfo announcement endpoint stable for long-term use?
**Status:** Endpoint validated (2026-06-01), but stability unknown
**Impact:** Affects reliability of announcement data

### 8. Cninfo orgId Inference Accuracy
**Question:** Is the orgId inference logic (gssz/gssh + ticker) always correct?
**Status:** Validated for 000001 and 600519, but not comprehensive
**Impact:** May need lookup table for accuracy

### 9. Cninfo Rate Limit
**Question:** What are the rate limits for Cninfo announcement API?
**Status:** Conservative usage recommended (1 req/sec)
**Impact:** Affects bulk announcement fetching

### 10. PDF Download Requirement
**Question:** Is PDF download needed for future Disclosure Guard?
**Status:** Not implemented, deferred
**Impact:** May need PDF parsing for risk assessment

### 11. Async/Concurrency Worker
**Question:** Does orchestration need async worker for concurrent provider calls?
**Status:** Not implemented, current is serial
**Impact:** May improve performance for multi-provider requests

### 12. Provider Priority / Fallback Order
**Question:** Should orchestration support provider priority or fallback?
**Status:** Not implemented
**Impact:** Could improve data availability when primary provider fails

### 13. Persistent Provider Run Manifest
**Question:** Should orchestration results be persisted for audit?
**Status:** Not implemented
**Impact:** Could improve debugging and audit trail

### 14. Orchestration → Market-Wide Scan Integration
**Question:** How should orchestration connect to Market-Wide Scan?
**Status:** Not implemented
**Impact:** Required for Phase 5A

---

## Resolved Questions

### Tencent API Endpoints
**Question:** What are the specific Tencent Finance API endpoints?
**Status:** ✅ Resolved (2026-06-01)
**Result:** https://qt.gtimg.cn/q={symbol} (GET, GBK, ~ separator, 88 fields)
**Confirmed fields:** turnover_rate(38), pe_ratio(39), market_cap(44,45), pb_ratio(46), limit_price(47,48)

### Cninfo API Access
**Question:** Does Cninfo require API key?
**Status:** ✅ Resolved (2026-06-01)
**Result:** No API key required, public endpoint
**Endpoint:** http://www.cninfo.com.cn/new/hisAnnouncement/query (POST)
**Parameters:** stock=<code>,<orgId>
