# Legacy Data Policy

**Date:** 2026-06-01
**Status:** Active

---

## Policy

### Default Behavior

Legacy data is **not committed** to the repository by default.

### What is Legacy Data?

- Historical hotlist data from user's previous project (`tradingagents-old`)
- User's manual hotlist inputs
- Generated attention pool outputs
- Import audit reports
- Reference data generated from user's local environment

### Why Not Commit?

1. **User Privacy:** Legacy data contains user's historical trading observations
2. **Local Relevance:** Data is specific to user's local environment
3. **Generated Content:** Attention pool and audit reports are generated outputs
4. **Test Independence:** Tests should not depend on user's private data

### What Can Be Committed?

- **Stock name map:** Reference data useful for all environments (if user approves)
- **Sample fixtures:** Small, anonymized samples for testing (if needed)
- **Schema definitions:** Data structure definitions (already committed)

### Test Independence

- Tests must use mocks and fixtures, not real legacy data
- Tests must pass without any local data present
- CI/CD must not depend on user's private data

### If User Wants to Commit Legacy Data

1. User must explicitly approve
2. Create separate commit with clear message
3. Document in commit message what data is included
4. Ensure no sensitive information is included
5. Consider creating anonymized samples instead

---

## Current Status

| Data Type | Location | Committed? |
|-----------|----------|------------|
| Legacy import raw | data/manual_hotlists/legacy_import/raw/ | ❌ No |
| Legacy import structured | data/manual_hotlists/legacy_import/structured/ | ❌ No |
| Attention pool | data/manual_hotlists/attention_pool/ | ❌ No |
| Stock name map | data/reference/ | ❌ No |
| Audit reports | data/*/audit/ | ❌ No |
