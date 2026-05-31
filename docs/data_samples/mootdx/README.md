# mootdx Data Samples

## Purpose

This directory is for manual smoke test field auditing of the MootdxProvider.

## Important Notes

1. **Do not commit real raw payloads.** This directory is for documentation only.
2. **Do not treat samples as real-time market data.** Samples are for field structure reference.
3. **Smoke tests default to no network.** Use `--allow-network` to run manually.
4. **Real network results require human review.** Before using as provider field basis.

## Usage

Run smoke test (no network by default):
```bash
python scripts/smoke_test_mootdx_provider.py
```

Run smoke test with network (manual only):
```bash
python scripts/smoke_test_mootdx_provider.py --allow-network --symbol 600519.SH
```

## Files

- `FIELD_CHECKLIST.md` - Expected fields and validation checklist
- `README.md` - This file

## Validation Process

1. Run smoke test with `--allow-network`
2. Compare output against `FIELD_CHECKLIST.md`
3. Document any discrepancies
4. Update provider normalization if needed
5. Mark checklist items as verified

## Known Limitations

- mootdx depends on TDX server availability
- Order book completeness depends on mootdx response
- Beijing Exchange support unconfirmed
- as_of_time extraction may need refinement
