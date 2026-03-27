# Requirement Challenge — Round 8 of 8

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-27 11:46:42

---

我已经拿到任务说明，接下来只做这份提案的挑战性评估，不会加入额外格式或解释；现在在核对是否还有第 8 轮尚未解决的真实缺口。### VERDICT: CHANGES_REQUESTED

### SCORE: 8

### COMPLETENESS
- Release 1 scope: COVERED — Included and excluded surfaces are explicit and consistent with the latest stated direction.
- Import validation rules: COVERED — Matching, rollback, null semantics, rank checks, and cross-table consistency are defined clearly enough.
- Storage contract: GAP — `Storage Schema` is deferred as "same as v7", so this version is not self-contained and does not expose the exact columns, constraints, or indexes needed for implementation and review.
- Operational behavior: PARTIAL — Import failure handling is defined, but runtime behavior during a live SQLite write is not.
- Acceptance criteria: PARTIAL — Most validations are measurable, but the golden fixtures are not pinned to named schools/subjects/expected values.

### ISSUES
1. [major] Specification completeness — `Storage Schema` is referenced indirectly as "same as v7" instead of being written in this proposal — the current spec still lacks explicit table definitions, uniqueness rules, foreign-key behavior, and indexes, which makes implementation and verification inconsistent across engineers.
2. [major] Boundary conditions — the importer performs transactional `DELETE+INSERT`, but the proposal does not state whether this runs only in a maintenance window or against a live SQLite-backed API — define the operating mode, or require WAL/timeout/retry behavior so reads do not fail with locking errors.
3. [minor] Testability — "golden data (3 schools + 2 subjects)" is a good safeguard, but the exact fixtures are not named — specify the fixed schools, subjects, and expected values/checksums so acceptance tests are reproducible.
4. [question] For user — Is this importer allowed to be an offline admin task with temporary API unavailability, or must it run safely while the site remains readable?

### SCENARIOS_ASSESSMENT
- Scenario 1: NEEDS_WORK — The extraction/import flow is strong, but it still depends on an external schema reference and leaves concurrent read/write behavior undefined.
- Scenario 2: WELL_DEFINED — `NULL -> "-"` and null-last sorting provide a concrete list-page behavior for both covered and uncovered schools.
- Scenario 3: WELL_DEFINED — Hiding the whole section when absent, hiding null fields selectively when present, and labeling the year give a clear detail-page contract.

### ARCHITECTURE_ASSESSMENT
- Fitness: 8
- Risks: [`v8 is not self-contained because schema details are externalized to v7`, `SQLite locking behavior during import is unspecified`, `golden-data checks are not yet fully reproducible`]
- Suggestions: [`Inline the exact DDL, constraints, and indexes in v8`, `Declare whether imports are offline-only or live-safe and specify the SQLite strategy accordingly`, `Pin named golden fixtures with expected values/checksums in the acceptance criteria`]

### SUMMARY
This proposal is very close to approval and already resolves the major semantic and integrity gaps from earlier rounds, but it is not fully implementation-ready as written. The remaining blockers are not business-scope problems; they are specification completeness and runtime-boundary problems: the schema is still indirect, and the behavior of a SQLite import under concurrent reads is undefined. Once those are made explicit and the golden fixtures are named, the Release 1 spec should be approvable.
