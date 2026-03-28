# Requirement Challenge — Round 2 of 2

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-28 14:05:07

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 6

### COMPLETENESS
- User flows: PARTIAL — Batch crawl, resume, dry-run, merge, and no-data handling are present, but deterministic batch slicing across repeated runs is not defined.
- Ambiguity: GAP — The proposal leaves `--offset` ordering, unique-key assumptions, and parser-failure semantics implicit even though correctness depends on them.
- Architecture fit: PARTIAL — Worktree + SQLite snapshot + sequential crawling is a good fit for the requirement, but the merge and retry model is still too weak for a multi-day production run.
- Boundary conditions: PARTIAL — There is no fail-fast rule for target-school count mismatch, zero-result queries, invalid `--batch-size`/`--offset`, or schema/version drift during the crawl window.
- Dependency risks: PARTIAL — HTTP 403/500 and timeouts are covered, but layout drift, prolonged blocking/rate limiting, browser degradation over long runs, and snapshot staleness are not fully addressed.
- Testability: PARTIAL — Dry-run and a 50-school pilot are useful, but merge correctness, idempotency, and failure classification are not specified in a measurable way.
- Scope control: COVERED — The proposal stays close to the original requirement; the added status field and merge script are still directly in service of the batch crawl.

### ISSUES
1. [critical] Batch partitioning — The proposal never defines whether `--offset` is applied before or after filtering out `success/no_data` records. In a resumable multi-day crawl, that can skip untouched schools or reprocess the wrong slice, so full coverage of all 569 schools is not guaranteed.
2. [critical] Data integrity — Treating “HTML structure changed but parse failed” as `warning + success` is unsafe. That would permanently suppress retries for corrupted or incomplete data and hide parser regressions behind a success state.
3. [major] Merge/idempotency — `INSERT OR REPLACE` and `INSERT OR IGNORE` are only safe if the four crawler tables have the correct unique constraints and a defined conflict policy. Those schema assumptions are not stated, and the proposed merge acceptance check (`scrape_log` row count >= worktree row count + 5-school sample) is too weak to detect silent drops or stale rows.
4. [major] Boundary handling — `Found {N} target schools (expected ~569)` is informational only. The plan does not say whether the crawl must stop, warn, or continue when N is materially wrong, nor how invalid `--batch-size`/`--offset` values should be rejected.
5. [question] For user — Should this 3-4 day crawl use a fixed snapshot of the `schools` table copied on day 1, or must each batch refresh school master data from the main DB? That trade-off between reproducibility and freshness is a product decision, not an implementation detail.

### SCENARIOS_ASSESSMENT
- Batch crawl: NEEDS_WORK — The happy path is clear, but batch determinism, parameter validation, and fail-fast rules for unexpected school counts are missing.
- Resume after interruption: NEEDS_WORK — Resume intent is clear, but behavior for partial writes, transaction boundaries, and batch slicing across retries is not defined.
- Data merge: NEEDS_WORK — Backup/restore intent is good, but conflict resolution, schema compatibility, and measurable reconciliation are under-specified.
- Dry-run preview: WELL_DEFINED — The purpose and expected “no HTTP requests” behavior are concrete.
- No-data school handling: NEEDS_WORK — Permanent `no_data` skipping is reasonable, but the `<2 tables` detector is brittle and may confuse template changes with genuine absence of data.

### ARCHITECTURE_ASSESSMENT
- Fitness: 6/10
- Risks: [non-deterministic batch coverage because `offset` semantics are undefined, silent data loss because parse failures can be marked as success, merge safety depends on undocumented unique keys/conflict rules, external site layout/blocking changes can stall or poison a multi-day run, copied DB snapshot may become stale while the main DB continues evolving]
- Suggestions: [define batching on a stable ordered school list before resume filtering or persist explicit batch manifests, treat parse/structure errors as retryable or manual-review states instead of success, document required unique constraints and transaction boundaries for all four crawler tables, strengthen merge validation with per-table inserted/updated counts and deterministic reconciliation queries, add fail-fast checks for unexpected target-school counts and invalid CLI parameters, decide explicitly whether the crawl uses a frozen snapshot or refreshed school master data]

### SUMMARY
The proposal is much closer to executable than round 1, and the overall direction is sensible: sequential crawling, worktree isolation, backups, and resumability all fit the original requirement. However, it is not yet production-ready because two correctness risks remain unresolved: batch boundaries are not deterministic across resumed runs, and parse failures can be misclassified as success. Until those are fixed, plus stronger merge/idempotency guarantees are specified, the architecture can still silently miss schools or mark bad data as complete.
