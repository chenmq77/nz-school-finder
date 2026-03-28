# Implementation Review — Round 1 of 2

**Model**: gpt-5.4-xhigh-fast
**Stack**: backend
**Files**: crawlers/ncea_crawler.py,crawlers/batch_ncea.py,scripts/merge_db.py
**Date**: 2026-03-28 14:32:06

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 5

### REQUIREMENT_COVERAGE
- [Dynamic target-school discovery and deterministic `--offset` / `--batch-size` slicing]: IMPLEMENTED — `get_target_schools()` queries secondary/composite schools ordered by `school_number`, and slicing is applied before resume filtering.
- [Resume behavior for `success` / `no_data` vs retryable statuses]: PARTIAL — `get_completed_metrics()` correctly skips `success` and `no_data`, but the implementation assumes the new `status` column already exists and does not deliver the required schema/backfill migration.
- [Dry-run preview output]: PARTIAL — `--dry-run` avoids crawling and prints an ETA, but it does not print the required aggregate completed-school and pending-school counts.
- [`no_data` classification and permanent skip]: PARTIAL — the visible crawler path records `no_data` when fewer than two tables are found, and batch resume would skip that metric later, but the overall status-driven behavior is incomplete because the circuit-breaker logic is not tied to metric statuses.
- [Circuit breaker after 5 consecutive `failed` / `timeout` results]: NOT_IMPLEMENTED — the breaker is driven by school-level exceptions, not by consecutive retryable metric outcomes in `scrape_log`.
- [Automatic database backup before batch crawl]: IMPLEMENTED — `auto_backup_db()` is called before the batch starts.
- [School-count validation rules]: PARTIAL — `--strict` exists, but non-strict warnings do not follow the explicit `<500` / `>650` thresholds from the spec.
- [Merge core flow with backup, `ATTACH`, `INSERT OR IGNORE`, and per-table stats]: IMPLEMENTED — the merge script backs up the target DB, attaches the source DB, merges the four tables, and prints before/after/delta counts.
- [Working `--verify` merge mode]: NOT_IMPLEMENTED — the current verification path double-attaches `src` and fails before performing the required verification.
- [Schema migration for `scrape_log.status` plus legacy backfill]: NOT_IMPLEMENTED — there is no delivered migration step that adds `status` and maps legacy `success` values to the new status taxonomy.
- [Post-merge acceptance checks]: PARTIAL — the script prints table counts, but it does not implement the specified `scrape_log` row check or sampled school-level data consistency verification.

### ARCHITECTURE_REVIEW
- Frontend: 10 — Out of scope for this backend-only crawler/merge task; no frontend contract is introduced here.
- Backend: 5 — Splitting responsibilities across crawler, batch runner, and merge utility is directionally correct, but migration handling, breaker semantics, and verification flow are not production-safe yet.
- Integration: 4 — The main integration contract is SQLite schema/data exchange, and it is brittle because all consumers assume `scrape_log.status` exists while `--verify` currently breaks on DB attachment lifecycle.
- Overall fitness: 5

### ISSUES
1. [major] [backend] `scripts/merge_db.py:141` — `--verify` is broken because `merge()` attaches `src` and then calls `verify_merge()`, which attaches the same alias again; the required verification path will raise `database src is already in use` instead of validating the merge. — Suggested fix: make exactly one function own the `ATTACH` / `DETACH` lifecycle for `src`, and have the verifier operate on that single attached handle.
2. [major] [integration] `crawlers/batch_ncea.py:64` — The batch runner hard-depends on `scrape_log.status`, but the required `ALTER TABLE` plus backfill from legacy `success` rows is not implemented anywhere in the delivered code, so existing databases can fail immediately. — Suggested fix: add an explicit migration script or startup migration that creates `status` when missing and backfills old rows before any batch or merge logic runs.
3. [major] [backend] `crawlers/batch_ncea.py:170` — The circuit breaker counts only uncaught school-level exceptions; it does not watch consecutive metric-level `failed` / `timeout` outcomes, so the crawler can violate the required “5 failures -> pause -> one retry -> abort” behavior. — Suggested fix: have `scrape_school()` return or persist per-metric statuses in a way the batch runner can evaluate, and drive the breaker from consecutive retryable statuses, resetting only on `success` or `no_data`.
4. [minor] [backend] `crawlers/batch_ncea.py:134` — `--dry-run` does not print the required aggregate completed-school and pending-school totals, so operators do not get the full preview requested by the spec. — Suggested fix: compute and print `{target_schools, completed_schools, pending_schools, estimated_time}` before returning from dry-run mode.

### MISSING_IMPLEMENTATIONS
- `scrape_log.status` schema migration and legacy data backfill from `success`.
- Metric-level circuit-breaker behavior based on consecutive `failed` / `timeout` results.
- A working `--verify` merge path.
- The required dry-run aggregate counts (`target`, `completed`, `pending`, `ETA`).
- The specified non-strict warning behavior for school counts outside the `500..650` range.
- The specified post-merge checks for `scrape_log` row dominance and sampled school-level data consistency.

### SUMMARY
The implementation is moving in the right architectural direction by separating scraping, batch orchestration, and DB merge concerns, but it is not ready for approval yet. The most important gaps are operational rather than structural: the required schema migration is missing, the circuit breaker does not enforce the specified failure policy, and the mandatory `--verify` merge path is currently unusable. Those issues affect core correctness and reliability for a 569-school batch crawl, so another iteration is required before this can be considered production-ready.
