# Requirement Challenge — Round 5 of 8

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-26 23:12:46

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 7

### COMPLETENESS
- Core flows: PARTIAL — extraction/import, list rendering, and detail rendering are defined, but ranking-only schools outside the matched school set still have no consistent handling.
- Data semantics: PARTIAL — year separation is clear, but `outstanding_merit` and `distinction` are assumed to be percentages without an explicit source-backed definition.
- Error handling: COVERED — checksum gating, ambiguous-match fail-fast, rollback, and no-data API behavior are specified.
- Acceptance criteria: GAP — current validations are mostly range-based and do not prove that parsed values are attached to the correct school and column.

### ISSUES
1. [critical] Architecture / data model — The proposal says subject Top10 entries may exist without a summary row, but `school_subject_ranking` still requires a resolved `school_number`. That means ranking-only schools outside the canonical matched set cannot be stored or validated consistently. Define one explicit rule: drop unmatched ranking-only schools, add a raw-name staging/reference table, or expand the canonical school set.
2. [major] Data semantics — `outstanding_merit` and `distinction` are modeled as `REAL` percentages, but the requirement text does not define whether these are counts, percentages, or percentages of which cohort. Lock down the unit and denominator from the PDF and reflect that in DB/API/UI naming.
3. [major] Testability — Range checks and row-count assertions will not catch a parser that shifts columns or attaches a valid numeric row to the wrong school. Add checksum-pinned acceptance checks for a small set of known schools/subjects plus explicit expected import counts for this PDF checksum.
4. [question] For user — If a subject Top10 school appears in the PDF but is not present in the current `schools` dataset, should Release 1 ignore it, keep it as reference-only ranking data, or expand the product scope to support those schools?

### SCENARIOS_ASSESSMENT
- Scenario 1 (data extraction and import): NEEDS_WORK — the import sequence is mostly clear, but ranking-only schools and stronger parser acceptance checks are still underdefined.
- Scenario 2 (list page UE column): WELL_DEFINED — display, empty state, and sort placement are concrete and proportionate to Release 1.
- Scenario 3 (detail page NCEA section): NEEDS_WORK — visibility and year labeling are clear, but metric units and the exact behavior of subject rankings for non-canonical schools are still ambiguous.

### ARCHITECTURE_ASSESSMENT
- Fitness: 7/10
- Risks: [`school_subject_ranking` cannot represent unmatched ranking-only schools, metric units for `outstanding_merit`/`distinction` may be wrong, parser drift can pass numeric validation and silently import incorrect data]
- Suggestions: [choose one explicit policy for ranking-only schools, define metric units and denominators in the contract, add checksum-pinned golden-data assertions, scope `DELETE` operations by `source` and `data_year` during re-import]

### SUMMARY
The proposal is close to implementation-ready and stays within the agreed Release 1 scope, but it is not fully converged yet because one declared scenario is not representable by the current schema, two metrics still rely on an unstated semantic assumption, and the validation strategy is not strong enough to detect silent-but-plausible parsing errors. Resolve those points and the spec should be ready for approval.
