# Requirement Challenge — Round 4 of 20

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-27 15:53:18

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 7

### COMPLETENESS
- Parent course discovery flow: COVERED — overview tree, zero-count behavior, count calculation, and drill-down to a filtered school list are all described.
- Vocational pathways display: COVERED — informational-only scope, data source, and deferred mapping boundary are clear.
- NZQA taxonomy fidelity: PARTIAL — the proposal says official order, level-specific markers, and Te Reo medium variants matter, but the data model does not yet define how those are stored or validated.
- Crawler matching requirement: PARTIAL — synonym and abbreviation support is covered via aliases, but the original "improve fuzzy matching" requirement has effectively been narrowed to exact match plus manual alias review.
- Partial-data communication: GAP — counts are based only on crawled schools, but the UI/API behavior does not say how users are warned that this is not a complete market view.

### ISSUES
1. [critical] Data modeling — `subject_alias.alias` is globally unique, so one school-specific custom course name can be forced to map to a single subject for every school; this creates a real false-positive risk as coverage expands. Add school-scoped aliases or an ambiguity path that falls back to `unmatched_subjects`.
2. [major] Requirement alignment — the original requirement asked for fuzzy matching improvements, but the proposal explicitly chooses "No fuzzy". If that is intentional, it needs explicit scope sign-off; otherwise add a minimal deterministic matching layer beyond aliases.
3. [major] Taxonomy modeling — official NZQA ordering, level-only subjects, and Te Reo medium equivalents are mentioned as required behaviors, but there are no explicit schema fields or seed rules that make those behaviors testable and repeatable.
4. [question] For user — should subject counts be explicitly labeled as "tracked/crawled schools only" to avoid implying full-market coverage, or is that product trade-off intentionally acceptable?

### SCENARIOS_ASSESSMENT
- Parent finds schools by course: NEEDS_WORK — the happy path is clear, but the filtered school-list contract and subset-coverage messaging are still implicit.
- Parent explores NZQA course system: NEEDS_WORK — the tree structure is defined, but subject placement for medium variants and level-specific subjects is still under-specified.
- Parent explores vocational pathways: WELL_DEFINED — scope, data source, and deferred boundaries are consistent.
- Crawler unmatched -> review -> backfill: NEEDS_WORK — the loop is clear, but global aliasing can incorrectly convert school-specific labels into permanent cross-school mappings.

### ARCHITECTURE_ASSESSMENT
- Fitness: 7/10
- Risks: [global alias collisions across schools, incomplete taxonomy metadata for official ordering and variants, user misreading subset counts as complete coverage, reduced first-pass recall if matching is alias-only]
- Suggestions: [allow school-scoped or ambiguous aliases, add explicit taxonomy metadata or seed rules for order/level/medium variants, decide and document subset-coverage labeling, either formalize "no fuzzy" as a signed-off scope change or add minimal heuristic matching]

### SUMMARY
The proposal is close and much stronger than earlier rounds, with the main flows, storage additions, and closed-loop review process now largely coherent. The remaining blockers are not broad rework items, but they are material: alias scope is too coarse for school-specific names, the stated matching strategy no longer cleanly matches the original fuzzy-matching requirement, and taxonomy edge cases are not yet modeled explicitly enough to guarantee a faithful NZQA-aligned overview.
