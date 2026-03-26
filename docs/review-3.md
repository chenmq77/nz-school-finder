# Requirement Challenge — Round 3 of 8

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-26 22:50:59

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 7

### COMPLETENESS
- Import workflow and rollback safety: COVERED — The happy path, failure path, rerun model, and transactional rollback are clearly defined for the core import flow.
- Data semantics and validation rules: GAP — The proposal still contains a logical contradiction around UE versus the mutually exclusive level buckets, so the validation contract is not yet reliable.
- School identity resolution: PARTIAL — Exact/normalized/manual mapping is defined, but ambiguous multi-match cases in the existing `schools` table are not handled.
- UI/API behavior for partial data: PARTIAL — List-page null handling is clear, but detail-page behavior for schools outside Metro coverage and subjects not in Top 10 is still underspecified.
- External dependency control: PARTIAL — The parser depends on a very specific PDF layout and file version, but there is no explicit checksum/version guard or failure rule for source-file drift.

### ISSUES
1. [critical] Data semantics — The line "`Below L1 + L1 + L2 + L3`, mutually exclusive, adding UE approximately 100%" is internally wrong because UE is not a separate mutually exclusive bucket from highest NCEA level; if implemented as written, valid data can fail validation and users can be misled — redefine the rule as `Below L1 + L1 + L2 + L3 ~= 100` with a rounding tolerance, and document the intended UE relationship separately.
2. [major] Matching — The matching strategy does not say what happens when an exact or normalized school name maps to multiple rows in `schools`; in a 2577-school dataset this can silently attach Metro data to the wrong school — treat multi-candidate matches as a hard failure and emit an explicit ambiguous-match report for manual resolution.
3. [major] Dependency risk — The design assumes one exact PDF structure and file version, but there is no guard against the wrong PDF, a revised Metro release, or extraction differences across PyMuPDF versions — pin the input filename/checksum and fail fast if the source file or extraction preconditions do not match the expected baseline.
4. [major] Detail-page contract — `school_subject_ranking` only stores positive Top 10 hits, but the UI/API behavior for a subject with no row is undefined, so consumers cannot tell "not in Metro Top 10" from "data missing / parse failed" — define an explicit response contract and rendering rule for absent rankings and out-of-coverage schools.
5. [question] For user — When a school has no Metro row, or a subject has no Top 10 ranking, should the product show explicit labels such as "Not covered by Metro 2025" / "Not in Top 10", or should those values stay hidden/blank?

### SCENARIOS_ASSESSMENT
- Scenario 1 (data extraction and import): NEEDS_WORK — The operational flow is strong, but ambiguous school matches and the incorrect UE validation relationship still make the import spec unsafe.
- Scenario 2 (list page UE column): WELL_DEFINED — The display, null state, and sort behavior are clear and measurable for Release 1.
- Scenario 3 (detail page NCEA overview): NEEDS_WORK — Core fields are listed, but subject-ranking empty states and no-coverage messaging are not defined well enough for implementation consistency.

### ARCHITECTURE_ASSESSMENT
- Fitness: 7
- Risks: [invalid validation caused by the UE/bucket contradiction; silent wrong-school linkage on ambiguous names; parser brittleness if the PDF file/version changes; unclear API semantics for non-ranked subjects and non-covered schools]
- Suggestions: [change validation to `Below L1 + L1 + L2 + L3 ~= 100` with explicit tolerance and separate UE checks; add hard-fail handling for ambiguous matches, not just unmatched ones; lock the source PDF by filename/checksum and document parser prerequisites; define API/UI semantics for "not covered" versus "not ranked" versus "missing data"]

### SUMMARY
The proposal is close to implementation-ready and is appropriately scoped for Release 1, but it is not fully converged yet. The remaining problems are not broad architecture rewrites; they are precision issues that can still cause incorrect imports or ambiguous UI behavior: the UE validation rule is logically wrong as written, ambiguous school-name collisions are not handled, and partial-data semantics for Top 10 rankings and Metro coverage need to be made explicit. Once those points are fixed, this should be ready to approve.
