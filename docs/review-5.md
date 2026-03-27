# Requirement Challenge — Round 5 of 20

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-27 15:56:31

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 7

### COMPLETENESS
- End-user browsing scenarios: COVERED — Scenario 1 and Scenario 3 are clearly described, with explicit click behavior, count logic, and zero-result presentation.
- Official taxonomy modeling: GAP — the proposal says it will align to NZQA and seed 97 subjects, but it still does not explicitly define the authoritative persisted Learning Area → Subject relationship or how the existing manual hierarchy is replaced/validated.
- Review loop and data maintenance: PARTIAL — the closed loop is present, but the persistence rules do not fully support normalized matching and conflict-free backfill.
- Failure and boundary handling: PARTIAL — API error messaging is defined, but empty seed state, partial seed state, and SQLite write-contention behavior are not.
- Dependency and version handling: PARTIAL — the proposal references an NZQA snapshot date, but there is no persisted versioning/audit mechanism for that taxonomy snapshot.
- Scope discipline: COVERED — the proposal stays broadly within scope; the added metadata supports taxonomy fidelity rather than introducing unrelated product features.

### ISSUES
1. [critical] Taxonomy model — the core requirement is correct NZQA Learning Area → Subject alignment, but the architecture still leaves that relationship implicit inside the legacy `subject_pool` structure. Adding `sort_order`, `ncea_level`, and `medium` does not by itself guarantee that the manual hierarchy is replaced or validated against an authoritative NZQA source.
2. [major] Data integrity — `subject_alias` uses `UNIQUE(alias, school_number)`, but in SQLite duplicate global aliases can still exist because `school_number = NULL` does not enforce uniqueness the way this design assumes; `unmatched_subjects` also deduplicates on raw text while matching is performed on normalized text. Add persisted normalized keys and SQLite-safe unique indexes for global vs school-scoped aliases.
3. [minor] Boundary conditions — the frontend has an API error banner, but the proposal does not define expected behavior when the NZQA seed is missing/partial or when crawler writes and review updates hit SQLite locking. Define minimum fallback responses and retry/transaction behavior.
4. [question] For user — when NZQA changes the official taxonomy after snapshot v1, should the product remain pinned to the old snapshot until an intentional migration, or should all schools be reclassified to the latest taxonomy on the next manual refresh?

### SCENARIOS_ASSESSMENT
- Scenario 1: WELL_DEFINED — the parent journey, count semantics, and clickability rules are concrete and testable.
- Scenario 2: NEEDS_WORK — the UI flow is clear, but the underlying source of truth for the official hierarchy is still not explicit enough to guarantee correctness.
- Scenario 3: WELL_DEFINED — the informational nature of vocational pathways and the deferred non-goal are clearly bounded.
- Scenario 4: NEEDS_WORK — the workflow exists, but normalized deduplication, alias conflict prevention, and crawl/review write contention are not fully specified.

### ARCHITECTURE_ASSESSMENT
- Fitness: 7
- Risks: [the official hierarchy may still depend on legacy manual structure rather than an explicit NZQA source of truth, global alias uniqueness is unsafe in SQLite with `NULL`-scoped keys, review/backfill quality can degrade when normalized matching is not reflected in persisted uniqueness rules]
- Suggestions: [make the Learning Area → Subject relationship explicit and versioned in persisted data or seed artifacts, add normalized columns plus separate unique indexes for global and school-specific aliases and for unmatched deduplication, define simple transaction/retry behavior and expected empty-state responses for seed/crawl/review edge cases]

### SUMMARY
This proposal is close to convergence and the user-facing flows are mostly solid, but it is not approval-ready yet because the most important requirement, authoritative NZQA taxonomy alignment, is still only partially modeled in the architecture. If the hierarchy source of truth is made explicit and the SQLite keying rules for aliases/unmatched records are tightened, the design would be much more reliable, testable, and ready for implementation without materially expanding scope.
