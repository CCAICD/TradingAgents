# Roadmap

## Phase 4: Data Provider Layer

### Phase 4A: Provider Infrastructure ✅
- ProviderResult schema
- BaseCnStockProvider
- RawPayloadStore
- RateLimiter
- ProviderRegistry
- LocalHotlistProvider
- ProviderResult → DataStatus conversion
- cn_stock_providers.yaml
- THIRD_PARTY_NOTICES.md

### Phase 4B: Mootdx Provider v0.1 ✅
- MootdxProvider implementation
- Supported datasets: daily_kline, minute_kline, index_kline, realtime_quote, order_book
- Lazy import mootdx
- Symbol normalization and market inference
- RateLimiter integration
- RawPayloadStore integration
- smoke_test_mootdx_provider.py
- 34 mock unit tests

### Phase 4B.1: Mootdx Smoke Test & Field Checklist ✅
- FIELD_CHECKLIST.md for mootdx datasets
- docs/data_samples/mootdx/README.md
- Smoke test defaults to no network
- Real smoke test failed (TDX connection issue)

### Phase 4C: Tencent Provider Skeleton ✅ → Phase 4E.4.1 Experimental ✅
- TencentProvider (inherits BaseCnStockProvider)
- Datasets: valuation, market_cap, turnover_rate, limit_price
- Endpoint validated (2 real requests)
- Experimental v0.1 implemented
- 27 mock unit tests

### Phase 4D: Cninfo Provider Skeleton ✅ → Phase 4E.3.2 Experimental ✅
- CninfoProvider (inherits BaseCnStockProvider)
- Dataset: announcement
- Endpoint validated (3 real requests)
- Experimental v0.1 implemented
- 18 mock unit tests

### Phase 4D.2: Provider Concurrency Policy ✅
- ProviderConcurrencyConfig
- External providers default max_concurrency=1
- Conservative rate limits

### Phase 4E: Endpoint Validation & Experimental Providers ✅
- Phase 4E.0: Provider endpoint research ✅
- Phase 4E.1: Provider validation harness ✅
- Phase 4E.2: Mootdx smoke test (failed - TDX connection) ⚠️
- Phase 4E.3: Cninfo endpoint validation ✅
- Phase 4E.3.1: Cninfo field sample confirmation ✅
- Phase 4E.3.2: CninfoProvider experimental v0.1 ✅
- Phase 4E.3.3: CninfoProvider safety audit ✅
- Phase 4E.4: Tencent endpoint validation ✅
- Phase 4E.4.1: TencentProvider experimental v0.1 ✅
- Phase 4E.4.2: TencentProvider safety audit ✅

### Phase 4F: Provider Orchestration / Freshness Aggregation ⏳ (Recommended Next)
- Provider result aggregation
- DataFreshnessGuard auto-summary
- Multi-provider coordination
- Not yet implemented

### Phase 4G: Eastmoney Provider (Deferred)
- Planned for future
- Not yet implemented

---

## Phase 5: Real Data Integration

### Phase 5A: Market-Wide Scan Real Data ⏳
- Connect providers to Market-Wide Scan schema
- Real-time market breadth data
- Sector data integration

### Phase 5B: Theme Detection Real Data ⏳
- Connect data sources to Theme Detection
- Real theme scoring

### Phase 5C: Candidate Selection Real Data ⏳
- Connect data sources to Candidate Selection
- Real candidate scoring

---

## Phase 6: Guards

### Phase 6A: Disclosure Guard / Negative Event Guard ⏳
- Connect Cninfo provider
- Announcement risk assessment
- Block "no major negative" when data fails

### Phase 6B: Fundamental Risk Guard ⏳
- Connect fundamental data
- Financial risk assessment

---

## Phase 7: Reports

### Phase 7A: Post-Close Report MVP ⏳
- First real report using data pipeline

### Phase 7B: Pre-Close Report MVP ⏳
- End-of-day decision support

### Phase 7C: Next-Day Plan Report MVP ⏳
- Next day observation plan

---

## Phase 8: Reflection System ⏳
- Daily reflection
- Weekly/monthly/quarterly/yearly reflection
- Rule evolution
