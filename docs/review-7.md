# Requirement Challenge — Round 7 of 8

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-27 11:44:23

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 8

### COMPLETENESS
- Import pipeline: PARTIAL - The end-to-end extract, match, validate, and load flow is defined, but the ranking validation still allows silently incomplete Top 10 captures within an otherwise "complete" subject set.
- UI data states: PARTIAL - "No Metro data" and "full Metro data" are defined, but the spec does not define the rankings-only state if a school appears in subject rankings but has no summary row.
- Failure handling: COVERED - Checksum gating, ambiguous matches, unmatched schools, and transaction rollback are all described as fail-fast paths.
- Scope control: COVERED - Release 1 stays limited to import, list UE, and detail-page NCEA display, with compare, trend, and regional features explicitly excluded.

### ISSUES
1. [critical] Validation - Subject ranking checks only assert "11 subjects" and "<=10 rows per subject", so a truncated extraction can still pass and publish incomplete Top 10 data - Bind expected row counts or contiguous rank sequences to the checksum-pinned PDF.
2. [major] Scenario boundary - The API/UI contract assumes Metro data means a summary row exists, but the architecture does not define what happens if a matched Auckland school appears in `school_subject_ranking` without `school_ncea_summary` - Either fail the import on this mismatch or define a rankings-only response/rendering state.
3. [minor] Data semantics - The 98-102 distribution rule is still an inferred assumption from the written field labels, not a source-verified rule in the spec - Add one explicit parser test or documented sample proving these percentages are mutually exclusive rather than cumulative.
4. [question] For user - If an Auckland school is found in the subject Top 10 pages but has no core-table row after matching, should Release 1 surface the ranking anyway or block the import until manual resolution?

### SCENARIOS_ASSESSMENT
- Scenario 1: NEEDS_WORK - The import workflow is solid overall, but it does not fully prove ranking completeness and does not define cross-table consistency requirements.
- Scenario 2: WELL_DEFINED - UE display, null rendering, and sort placement are specific enough for implementation and testing.
- Scenario 3: NEEDS_WORK - The detail page handles null fields and no-data hiding, but it does not define the user experience when rankings exist without a summary row or what omitted subjects imply.

### ARCHITECTURE_ASSESSMENT
- Fitness: 8
- Risks: [silent partial subject imports, undefined rankings-without-summary state, incorrect level-distribution assumption in validation]
- Suggestions: [tighten ranking completeness assertions per subject, enforce or explicitly support summary/ranking consistency, add one source-verified acceptance test for the L1/L2/L3 semantics]

### SUMMARY
This proposal is close to approval and is appropriately scoped for Release 1, but it still has two meaningful data-integrity gaps: incomplete subject rankings can slip through validation, and the architecture does not define whether rankings can exist without a summary row. Resolving those boundaries, plus explicitly proving the level-distribution semantics, would make the spec measurably safer and easier to approve.
