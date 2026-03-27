# Requirement Challenge — Round 1 of 20

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-27 13:28:25

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 6

### COMPLETENESS
- Official taxonomy alignment: PARTIAL — the proposal says it will align to NZQA, but it does not define the exact authoritative source, snapshot/versioning strategy, or how "complete" will be verified.
- Course discovery flow: PARTIAL — the overview-to-school-list flow is covered, but unique-school counting rules, zero-count meaning, and the filtered-list contract are not defined.
- Unmatched course handling: PARTIAL — capture is covered, but the storage target conflicts with the stated user decision, and deduplication/review mechanics are missing.
- Vocational pathway display: PARTIAL — independent display is covered, but the exact card metrics, empty states, and data provenance are unclear.
- Delivery and backfill: GAP — the plan does not explain how to avoid showing incomplete or misleading data before recrawl/backfill finishes.

### ISSUES
1. [critical] Data semantics — the proposal never defines whether subject counts mean distinct schools or raw course rows, so one school could be counted multiple times when several course variants map to the same subject — define aggregation rules and validate them with examples.
2. [major] External dependency — "align with NZQA official classification" is not operationalized: the exact NZQA source, extraction method, update cadence, and fallback when the source changes are missing — pin an authoritative dataset or snapshot and version it.
3. [major] Requirement alignment — the design creates `unmatched_subjects`, but the stated user decision says unmatched records go to a raw table; the proposal does not reconcile this contradiction — choose one canonical storage model and document why.
4. [major] Architecture integrity — `subject_pool` still allows invalid parent-child relationships and deeper nesting, so the promised two-level Learning Area → Subject hierarchy is not actually enforced — add validation or migration rules that reject invalid structures.
5. [major] Operational workflow — scenario 4 says manual review exists, but there is no defined review mechanism, deduplication policy, or resolution flow for repeated unmatched rows across recrawls — define the minimum review operations and dedupe keys.
6. [major] Scope/data mismatch — the vocational pathway cards now include "student statistics", but the original requirement only asked for independent display and the proposal does not specify what statistics exist in current tables — either reduce the card scope to supported metrics or define exact field meanings and sources.
7. [major] Release sequencing — the overview page can be shipped before recrawl/backfill, which means the UI may present incomplete counts while claiming NZQA completeness — gate rollout on coverage thresholds or show a clear partial-data status.
8. [minor] Scope creep — the search bar is newly introduced without corresponding requirement, bilingual search behavior, or acceptance criteria — treat it as optional after the core overview flow is stable.
9. [question] For user — should zero-count NZQA subjects be visible as part of the official taxonomy, or hidden until at least one school is mapped?
10. [question] For user — do you want unmatched courses stored in a dedicated review table or appended to an existing raw ingestion table, and how much manual review overhead is acceptable at ~50 schools?
11. [question] For user — what exact metric should appear on each vocational pathway card: school count only, vocational achievement rate, or another business-defined KPI?

### SCENARIOS_ASSESSMENT
- Parent finds schools by course: NEEDS_WORK — the happy path is clear, but count semantics, zero-data meaning, and the filtered school-list contract are still undefined.
- Parent explores NZQA course system: NEEDS_WORK — the hierarchy display is covered, but "complete NZQA classification" is not measurable without a fixed authoritative source and update rule.
- Parent explores vocational pathways: NEEDS_WORK — independent display is covered, but the card contents, statistical definitions, and fallback behavior for missing data are unclear.
- Crawler encounters unmatched course: NEEDS_WORK — saving unmatched rows is covered, but review tooling, deduplication, and mapping resolution are missing.
- Partial-data rollout after taxonomy/mapping changes: MISSING — there is no scenario for what parents see while only part of the school set has been re-crawled.

### ARCHITECTURE_ASSESSMENT
- Fitness: 6/10
- Risks: [inflated or inconsistent school counts, unresolved unmatched-storage decision, fragile NZQA dependency handling, invalid hierarchy data, duplicate unmatched rows during recurring crawls, misleading partial-data UI before backfill completes]
- Suggestions: [define a versioned authoritative NZQA taxonomy source, specify distinct-school counting and school-list filter behavior, resolve raw-table vs dedicated-table storage, enforce the two-level hierarchy with validation, define a minimal unmatched-review workflow, limit vocational cards to data that already exists or explicitly model new metrics, gate release on recrawl/backfill coverage or show data freshness status]

### SUMMARY
The proposal is directionally strong and mostly aligned with the original goal, but it is not yet precise enough to be implementation-safe. The biggest gaps are around data semantics, authoritative taxonomy sourcing, contradictory unmatched-course storage decisions, and rollout behavior while data is still being remapped and backfilled. Tightening those areas would make the architecture much more reliable and testable without materially increasing scope.
