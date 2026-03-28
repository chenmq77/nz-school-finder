# Requirement Challenge — Round 1 of 2

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-28 14:00:28

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 5

### COMPLETENESS
- Batch execution flow: PARTIAL — batching, dry-run, and resume are described, but the plan assumes every school yields all five metrics and does not define valid partial outcomes.
- Missing-data handling: GAP — the requirement explicitly says some schools may have no NCEA data, but there is no terminal state, logging rule, or retry policy for that case.
- Merge and source-of-truth rules: GAP — the merge is described mechanically, but not semantically; there is no rule for how to handle main-DB changes during a multi-day crawl.
- Failure management: PARTIAL — a circuit breaker is mentioned, but the error classes, reset behavior, cooldown duration, and operator workflow are undefined.
- Backup and recovery: PARTIAL — backup creation is included, but overwrite behavior, restore steps, and failed-merge recovery are not specified.
- Acceptance and verification: PARTIAL — dry-run and row-count checks exist, but there are no measurable per-table, per-status, or per-school completion criteria.

### ISSUES
1. [critical] Requirements coverage — The proposal does not define how a school with zero metrics or only partial metrics is recorded and considered complete — without explicit `success` / `no_data` / `failed` semantics, resume logic and acceptance criteria will be incorrect.
2. [critical] Data consistency — The architecture allows normal work to continue in the main directory while a multi-day crawl runs in a worktree, but the merge plan assumes a static destination DB — `ATTACH` + `INSERT OR IGNORE` does not resolve concurrent changes, freshness, or conflicting `scrape_log` rows.
3. [major] Contradictory write policy — The original proposal uses `INSERT OR IGNORE` for merge, while the architecture section claims `INSERT OR REPLACE` for idempotency — these have different overwrite semantics and can materially change data, so the policy must be chosen explicitly per table.
4. [major] Failure model gap — The circuit breaker only covers “3 consecutive 403/500” — it does not address timeouts, browser crashes, HTML changes, DNS/network errors, reset conditions, or whether the threshold is per page, per school, or global.
5. [major] School-selection ambiguity — “Query 569 secondary/composite schools from DB” is too vague — the exact filter, snapshot behavior, and expected handling when the query returns fewer or more than 569 are not defined.
6. [major] Weak acceptance criteria — “50 schools’ 5 metrics all stored” conflicts with the stated requirement that some schools may legitimately have no NCEA data, and “row count equals worktree DB” is not sufficient to prove a correct merge.
7. [minor] Backup design — `schools_backup_YYYYMMDD.db` can be overwritten by multiple same-day runs, and there is no explicit restore procedure if a batch or merge fails partway through.
8. [minor] Scope/compliance risk — adding “User-Agent spoofing” is outside the original requirement and may be inappropriate for a polite government-site crawler unless the user explicitly approves that behavior.
9. [question] For user — If a school has no data for one or more metrics, should that be treated as a successful terminal state and skipped on future runs, or should it be retried periodically?
10. [question] For user — During the 3-4 day crawl, is the main DB allowed to keep receiving other changes, or should it be frozen until the worktree data is merged back?

### SCENARIOS_ASSESSMENT
- Batch crawl: NEEDS_WORK — the happy path is clear, but completion rules for partial/no-data schools and out-of-range `--batch-size` / `--offset` behavior are missing.
- Resume after interruption: NEEDS_WORK — resume depends on `scrape_log`, but the proposal does not define durable status types or a safe recovery strategy when logs are incomplete or corrupted.
- Data merge back to main DB: NEEDS_WORK — the mechanics are simple, but the plan is unsafe unless DB ownership and conflict rules are defined first.
- Dry-run planning: WELL_DEFINED — it is clearly non-mutating and useful, though it should explicitly report filtered target counts and skipped reasons.
- Missing/partial-data schools: MISSING — this is an explicit requirement constraint, but there is no concrete flow or acceptance rule covering it.

### ARCHITECTURE_ASSESSMENT
- Fitness: 5
- Risks: [undefined no-data completion semantics, silent merge conflicts after multi-day DB divergence, contradictory `IGNORE` vs `REPLACE` behavior, incomplete circuit-breaker definition, assumption that only `batch_ncea.py` must change]
- Suggestions: [define explicit crawl statuses such as `success`, `no_data`, `failed`, and `retryable`, specify the exact school-selection query and expected count handling, define DB ownership and merge rules before allowing parallel main-DB work, use timestamped backups plus a documented restore path, replace vague acceptance criteria with measurable per-table and per-status checks]

### SUMMARY
The proposal is directionally sound and mostly stays within the original scope, but it is not yet production-ready because the most important operational semantics are still undefined: how to treat schools with missing data, how resume state is modeled, and how a multi-day worktree crawl safely merges into a potentially changing main database. Until those behaviors are made explicit and testable, the architecture remains brittle and the acceptance criteria are not reliable.
