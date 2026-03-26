# Requirement Challenge — Round 4 of 8

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-26 23:02:01

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 7

### COMPLETENESS
- Core extraction workflow: COVERED — source pages, matching order, transaction behavior, and validation checks are concrete enough to implement.
- Cross-section data consistency: GAP — the spec does not state whether every school appearing in subject Top 10 pages must also exist in `school_ncea_summary`, or what to do if that invariant fails.
- UI/API boundary behavior: PARTIAL — list/detail rendering rules are mostly defined, but the exact backend contract for no-data and partial-data responses is still implicit.
- Release scope versus original comparison goal: GAP — Release 1 excludes compare-page integration even though the original requirement frames this as an enhancement to the comparison system.

### ISSUES
1. [critical] API contract / data integrity — `/api/school/{num}/ncea` is underspecified for no-summary, no-ranking, and ranking-only cases — define exact response shape/status codes and whether rankings are valid without a summary row.
2. [major] Data semantics — the UI only requires a generic source label, but the dataset mixes `2023` NCEA outcomes with `July 2024` roll data — require explicit year/date labeling in the UI so users do not compare mixed-vintage numbers as if they were from the same period.
3. [minor] Operability — checksum validation protects the input file before import, but the imported checksum/file version/timestamp is not persisted — storing import provenance would make later troubleshooting and re-verification much easier.
4. [question] For user — Is Release 1 allowed to stop at list/detail integration, or must NCEA data also appear in the compare workflow to satisfy the original "comparison system" objective?

### SCENARIOS_ASSESSMENT
- [Scenario 1: Data extraction and import]: NEEDS_WORK — the main import path is strong, but it still needs an explicit rule for summary-versus-ranking consistency and how that rule is validated.
- [Scenario 2: List page UE column]: WELL_DEFINED — display behavior, missing-data rendering, and sorting intent are clear enough for implementation.
- [Scenario 3: Detail page NCEA overview]: NEEDS_WORK — panel visibility rules are clear, but the backend contract for no-data/partial-data cases and the mixed-year presentation are not fully defined.

### ARCHITECTURE_ASSESSMENT
- Fitness: 7
- Risks: [undefined no-data/partial-data API contract, silent hiding of ranking-only schools, mixed-year metrics being misread by users, scope reduction not yet explicitly approved]
- Suggestions: [define exact `/api/school/{num}/ncea` response shapes and status codes, enforce or explicitly support ranking-only records during import, label `2023 NCEA` and `July 2024 roll` explicitly in the UI, get explicit user sign-off on excluding compare-page delivery from Release 1]

### SUMMARY
The proposal is close and most previously critical gaps appear resolved, especially around UE validation, checksum guarding, and ambiguous school matching. The remaining blockers are now boundary and contract issues rather than extraction logic: the spec still needs a precise no-data/partial-data API contract, an explicit rule for summary-versus-ranking consistency, and a clear user decision on whether excluding compare-page integration is acceptable for this release.
