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

### 4. Tencent API Endpoints
**Question:** What are the specific Tencent Finance API endpoints for valuation, market_cap, turnover_rate, limit_price?
**Status:** Pending research
**Impact:** TencentProvider implementation

### 5. Cninfo API Access
**Question:** Does Cninfo require API key? What are the rate limits?
**Status:** Pending research
**Impact:** CninfoProvider implementation

### 6. Order Book Field Names
**Question:** What are the exact field names mootdx returns for bid/ask data?
**Status:** Pending smoke test
**Impact:** order_book normalization

### 7. as_of_time Extraction
**Question:** What datetime format does mootdx use in different datasets?
**Status:** Pending smoke test
**Impact:** DataFreshnessGuard accuracy

---

## Resolved Questions

(None yet)
