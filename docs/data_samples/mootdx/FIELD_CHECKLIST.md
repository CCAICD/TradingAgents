# mootdx Field Checklist

## daily_kline

**Expected Fields:**
- open (float)
- close (float)
- high (float)
- low (float)
- volume (int/float)
- amount (float)
- datetime (str, format: "YYYY-MM-DD HH:MM:SS")

**Checks:**
- [ ] All fields present
- [ ] No null values
- [ ] datetime is parseable
- [ ] as_of_time can be extracted from last record
- [ ] fetched_at exists
- [ ] raw_payload_path exists
- [ ] ProviderResult status is success
- [ ] DataStatus converts to fresh

---

## minute_kline

**Expected Fields:**
- open (float)
- close (float)
- high (float)
- low (float)
- volume (int/float)
- amount (float)
- datetime (str, format: "YYYY-MM-DD HH:MM:SS")

**Checks:**
- [ ] All fields present
- [ ] No null values
- [ ] datetime is parseable
- [ ] as_of_time can be extracted
- [ ] fetched_at exists
- [ ] raw_payload_path exists
- [ ] ProviderResult status is success
- [ ] DataStatus converts to fresh

---

## index_kline

**Expected Fields:**
- open (float)
- close (float)
- high (float)
- low (float)
- volume (int/float)
- amount (float)
- datetime (str, format: "YYYY-MM-DD HH:MM:SS")

**Checks:**
- [ ] All fields present
- [ ] No null values
- [ ] datetime is parseable
- [ ] as_of_time can be extracted
- [ ] fetched_at exists
- [ ] raw_payload_path exists
- [ ] ProviderResult status is success
- [ ] DataStatus converts to fresh

---

## realtime_quote

**Expected Fields:**
- code (str)
- name (str)
- price (float)
- open (float)
- high (float)
- low (float)
- volume (int/float)
- amount (float)
- datetime (str)

**Optional Fields (for order_book):**
- bid1, bid1_volume
- bid2, bid2_volume
- bid3, bid3_volume
- bid4, bid4_volume
- bid5, bid5_volume
- ask1, ask1_volume
- ask2, ask2_volume
- ask3, ask3_volume
- ask4, ask4_volume
- ask5, ask5_volume

**Checks:**
- [ ] All required fields present
- [ ] No null values
- [ ] datetime is parseable
- [ ] as_of_time = fetched_at (real-time)
- [ ] fetched_at exists
- [ ] raw_payload_path exists
- [ ] ProviderResult status is success
- [ ] DataStatus converts to fresh

---

## order_book

**Expected Fields:**
- All realtime_quote fields
- bid1-bid5 with volumes
- ask1-ask5 with volumes

**Checks:**
- [ ] bid/ask fields present
- [ ] If bid/ask missing, status is partial
- [ ] Warning added if partial
- [ ] has_order_book metadata correct
- [ ] fetched_at exists
- [ ] raw_payload_path exists

---

## General Checks

- [ ] as_of_time is extractable from data
- [ ] fetched_at is present
- [ ] raw_payload_path is generated
- [ ] warnings are reasonable
- [ ] DataStatus conversion is correct
- [ ] Beijing Exchange symbols produce warning
- [ ] Unknown symbols produce warning
- [ ] No buy/sell fields in output

---

## Pending Real Smoke Test

- [ ] Actual mootdx field names
- [ ] Actual datetime format
- [ ] Order book completeness
- [ ] Beijing Exchange support
- [ ] Server availability
