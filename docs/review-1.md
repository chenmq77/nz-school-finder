# Requirement Challenge — Round 1 of 8

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-26 22:04:09

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 5

### COMPLETENESS
- [School-level extraction]: PARTIAL — the core table on pages 31-33 is covered, but the schema does not cleanly represent that some values are for 2023 while `school_roll` is explicitly for July 2024.
- [Subject ranking extraction]: PARTIAL — the 11 top-10 subject rankings are included, but tie handling, non-ranked schools, and validation expectations are not defined.
- [Comparison-system integration]: PARTIAL — list and detail pages are described, but the proposal does not define an actual multi-school comparison flow even though the requirement is to strengthen comparison capability.
- [School matching and referential integrity]: GAP — the proposal says all PDF schools should map to `schools`, but the acceptance target is only `>95%`, and no final policy exists for unmatched schools.
- [Regional/trend data scope]: GAP — pages 3-6 are listed as extractable data, but the proposal neither models them nor explicitly marks them out of scope.
- [Operational robustness]: GAP — reruns, transactions, partial failures, import auditability, and dependency failure behavior are not specified.

### ISSUES
1. [critical] Data model semantics — the proposed `school_ncea_summary.year` suggests a single time period, but the row mixes 2023 outcomes with a July 2024 roll count. This will create misleading API semantics unless metric periods are separated or explicitly modeled.
2. [critical] Mapping/completeness — the requirement says the PDF schools must be associated to the existing `schools` table, but the proposal accepts only `>95%` matching and does not define what happens to the remaining schools. Define whether import must fail, quarantine unmatched rows, or require manual mapping before release.
3. [major] Source-of-truth conflict — the system already has `school_performance` data for NCEA levels for 11 schools, but the proposal does not define which source wins when the Metro PDF differs. The API and UI need a canonical precedence rule per field.
4. [major] Scope ambiguity — the source overview includes regional summary/trend pages and the requirement mentions a comparison system, yet the proposal only specifies list/detail behavior and silently drops regional aggregates. Release-1 scope needs an explicit boundary.
5. [major] Import reliability — no idempotent import strategy, transaction boundary, rollback behavior, or import report is defined. A rerun or partial failure in SQLite could leave the dataset in an inconsistent state.
6. [minor] Schema/testability — `outstanding_merit` and `distinction` are typed as `TEXT` while comments imply percentages, and “data matches PDF” is not measurable. Use explicit numeric/raw-value rules and define concrete validation checks.
7. [question] For user — should release 1 include regional summary/trend insights and a dedicated comparison-page experience, or is the business priority limited to school-level summary data on list/detail pages only?

### SCENARIOS_ASSESSMENT
- [Scenario 1: data extraction and import]: NEEDS_WORK — the happy path is present, but rerun behavior, unmatched-school resolution, import atomicity, and hard pass/fail rules are missing.
- [Scenario 2: list-page UE comparison]: NEEDS_WORK — the column and sorting behavior are sketched, but null ordering, source labeling, and mixed-year labeling are undefined.
- [Scenario 3: school detail NCEA view]: NEEDS_WORK — the displayed metrics are identified, but non-top10 subject behavior, conflicting legacy values, and user-facing provenance are not specified.
- [Scenario 4: school-to-school comparison flow]: MISSING — the proposal does not define how the new data improves the actual comparison experience beyond a sortable list column.
- [Scenario 5: regional/trend summary usage]: MISSING — pages 3-6 are acknowledged in the source data, but there is no user flow, schema, or API for them.

### ARCHITECTURE_ASSESSMENT
- Fitness: 5/10
- Risks: [mixed-period data stored under one year key, unresolved precedence against existing `school_performance` values, fragile school-name matching without a strict remediation workflow, non-idempotent/partial SQLite imports, unclear product scope for regional summaries and comparison UX]
- Suggestions: [separate metric periods or add explicit field-level period metadata, define a source-of-truth rule before API/UI integration, add transactional upsert plus unmatched-school audit/reporting, specify exact UI behavior for nulls/non-top10/ties and make it testable, get explicit product sign-off on whether regional pages 3-6 are in scope for release 1]

### SUMMARY
The proposal is directionally reasonable for extracting school-level Metro data, but it is not yet a production-ready specification. The biggest gaps are semantic correctness of the data model, the unresolved handling of unmatched schools and overlapping existing data, and unclear release boundaries around comparison UX and regional summary content. Once those decisions are made explicit and testable, the architecture can be implemented with much lower delivery and data-quality risk.
