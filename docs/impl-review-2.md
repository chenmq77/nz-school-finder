# Implementation Review — Round 2 of 2

**Model**: gpt-5.4-xhigh-fast
**Stack**: backend
**Files**: crawlers/ncea_crawler.py,crawlers/batch_ncea.py,scripts/merge_db.py
**Date**: 2026-03-28 14:41:36

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 5

### REQUIREMENT_COVERAGE
- Dynamic target-school query and deterministic `--offset` / `--batch-size` slicing: IMPLEMENTED — `get_target_schools()` uses the required secondary/composite query ordered by `school_number`, and slicing happens before resume filtering.
- `scrape_log.status` migration plus resume semantics (`success` / `no_data` skipped, `failed` / `timeout` / `parse_error` retried): PARTIAL — migration/backfill and skip logic exist, but whole-school startup failures can still bypass per-metric log persistence, so the required 5 log rows per school are not guaranteed.
- School-count validation and `--strict`: PARTIAL — the banner and warning behavior are present, but strict mode does not enforce the required `>10%` deviation rule.
- Circuit breaker (`5` consecutive `failed` / `timeout` -> `10m` pause -> one automatic retry -> abort on repeat): PARTIAL — failure counting and pausing exist, but the failed work item is not retried once as specified.
- Dry-run preview: IMPLEMENTED — the script prints target/completed/pending/ETA and exits before any crawl execution.
- `no_data` handling: IMPLEMENTED — `no_data` is logged, skipped on resume, and excluded from breaker counting because only `failed` and `timeout` increment the counter.
- Merge flow (`ATTACH` + `INSERT OR IGNORE` + per-table stats + pre-merge backup): IMPLEMENTED — the core merge mechanics are present.
- `--verify` completeness checks and merge failure recovery: PARTIAL — verification output exists, but it is too weak, its result is ignored, it does not perform the required sampled consistency validation, and failed verification does not restore the target DB.
- Completion-rate target `((success + no_data) / total) >= 95%`: NOT_IMPLEMENTED — no code computes or validates the required completion ratio.

### ARCHITECTURE_REVIEW
- Frontend: 8 — No frontend changes were in scope for this backend-only implementation.
- Backend: 5 — Responsibilities are split reasonably across crawler, batch coordinator, and merge script, but failure semantics and recovery guarantees are still incomplete.
- Integration: 4 — The crawler-to-log and source-DB-to-target-DB boundaries can still produce silently incomplete state.
- Overall fitness: 5

### ISSUES
1. [critical] [integration] `scripts/merge_db.py:144` — `merge()` commits before verification and ignores the boolean returned by `verify_merge()`, so `--verify` cannot stop a bad merge or trigger recovery even when validation fails. — suggested fix: run verification before the final commit, raise on verification failure, and automatically restore from the pre-merge backup.
2. [major] [integration] `scripts/merge_db.py:64` — `verify_merge()` only checks whether each source `school_number` exists somewhere in the target, which misses partial row loss for schools already present and does not satisfy the required sampled data-consistency check. — suggested fix: compare per-table row keys or per-school row counts/hashes and add the required sample-based data validation.
3. [major] [backend] `crawlers/batch_ncea.py:222` — the circuit breaker pauses after five failures but never retries the failed school/metric once as required; on the second trip it pauses again and only then aborts. — suggested fix: retain the failed work item, rerun it immediately after the first pause, and abort immediately if that retry fails again.
4. [major] [backend] `crawlers/batch_ncea.py:123` — `--strict` is tied to the `500-650` warning band instead of the specified `>10%` deviation rule, so counts like `500`, `512`, or `650` incorrectly continue. — suggested fix: keep `500-650` as a warning band, but separately abort in strict mode when `abs(count - 569) / 569 > 0.10`.
5. [major] [backend] `crawlers/ncea_crawler.py:230` — Playwright/browser startup happens outside the per-metric error-handling path, so a whole-school startup failure can exit before writing five `scrape_log` rows, breaking resume guarantees and the acceptance criterion. — suggested fix: wrap session startup in an outer `try/except` and persist `failed` / `timeout` log rows for every pending metric before returning or re-raising.

### MISSING_IMPLEMENTATIONS
- Automatic retry of the failed school/metric after the first circuit-breaker pause, with immediate abort if that retry fails again.
- Strict-mode abort when school-count deviation exceeds 10%, even if the count is still within `500-650`.
- Merge verification that proves per-table/per-school completeness and performs the required sampled data-consistency check.
- Automatic restoration from the pre-merge backup when verification fails.
- Guaranteed `scrape_log` coverage for all 5 metrics when browser/session startup fails before the per-metric loop.
- Completion-rate calculation/reporting for the `>=95%` requirement.

### SUMMARY
Several important round-1 items are now present, including dynamic school discovery, status migration, dry-run aggregate stats, deterministic slicing, and the basic merge pipeline. However, the implementation still misses two blocking guarantees for a full 569-school production crawl: safe/enforced post-merge verification with recovery, and the exact circuit-breaker/logging behavior required for reliable long-running resume semantics.
