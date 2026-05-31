# Acceptance Criteria

## Provider Requirements

1. **All providers must return ProviderResult.** No exceptions.
2. **ProviderResult must be convertible to DataStatus.** For DataFreshnessGuard integration.
3. **All external data must preserve raw_payload_path.** For audit and debugging.
4. **All tests must not depend on real network by default.** Network tests require explicit --allow-network.
5. **Failures must be explicit: failed/missing/stale/not_implemented.** No silent success.

## Report Requirements

6. **No buy/sell fields.** System is decision support, not trading execution.
7. **No forced replacements.** If no suitable replacement exists, say so clearly.
8. **Non-mainboard stocks not deleted, only marked.** Preserve market evidence.
9. **Announcement failure cannot claim "no major negative".** Must degrade report.
10. **Stale/failed data blocks strong conclusions.** Must degrade or block report.

## Data Quality

11. **All data must have metadata.** source, fetched_at, as_of_time, status, error_message.
12. **Raw payloads must be preserved.** For audit and debugging.
13. **Data freshness must be checked before formal reports.** DataFreshnessGuard required.
14. **No fabricated data.** Missing data must be reported honestly.

## Architecture

15. **All external data via provider adapters.** No direct third-party calls in business logic.
16. **A-stock rules in cn_stock only.** Must not pollute us_stock/crypto.
17. **ProviderResult → DataStatus → DataFreshnessGuard → Report.** Required chain.

## Concurrency

18. **New providers must declare rate_limit and concurrency strategy.** In cn_stock_providers.yaml.
19. **External providers default max_concurrency=1.** Conservative by default.
20. **Concurrency not increased without confirmation.** User/ChatGPT must approve.
21. **Failures must not be silent.** ProviderResult(status=failed) or partial required.
22. **Fetch results must be auditable.** raw_payload_path required.
23. **No uncontrolled parallel requests.** RateLimiter must be respected.
24. **Batch requests preferred over individual requests.** When provider supports it.
