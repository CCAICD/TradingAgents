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

### Phase 4B.1: Mootdx Smoke Test & Field Checklist 🔄
- Enhance smoke_test_mootdx_provider.py
- FIELD_CHECKLIST.md for mootdx datasets
- docs/data_samples/mootdx/README.md
- No real network tests tonight

### Phase 4C: Tencent Provider Skeleton ⏳
- TencentProvider (inherits BaseCnStockProvider)
- Datasets: valuation, market_cap, turnover_rate, limit_price
- Lazy HTTP (no default network)
- Mock unit tests
- Not implemented endpoints return not_implemented

### Phase 4D: Cninfo Provider Skeleton ⏳
- CninfoProvider (inherits BaseCnStockProvider)
- Dataset: announcement
- Announcement schema fields
- Lazy HTTP (no default network)
- Mock unit tests
- Not implemented endpoints return not_implemented

### Phase 4E: Eastmoney Provider (Deferred)
- Not tonight
- Planned for future

### Phase 4F: Provider Orchestration & Freshness Auto-Summary (Deferred)
- Not tonight
- Planned for future

---

## Phase 5: Real Data Integration

### Phase 5A: Market-Wide Scan Real Data ⏳
- Connect mootdx to Market-Wide Scan schema
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
