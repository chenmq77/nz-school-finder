# Requirement Challenge — Round 3 of 20

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-27 15:34:09

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 7

### COMPLETENESS
- Parent browse and filter flow: COVERED — Overview tree, school counts, zero-count behavior, and click-through to filtered school list are defined clearly enough.
- NZQA taxonomy alignment: PARTIAL — the source is named, but there is no measurable definition of what "fully aligned" means at a given snapshot date.
- Unmatched review and backfill loop: PARTIAL — capture and review are defined, but the reviewed mapping outcome does not automatically become reusable matching logic.
- Boundary conditions: PARTIAL — zero-count subjects are handled, but API failure, fully empty datasets, and duplicate raw-name normalization are still unspecified.
- Vocational pathways display: PARTIAL — the UI is simple and in scope, but the business rule for listing "related subjects" is not fully locked down.

### ISSUES
1. [critical] Crawler workflow persistence — `status='mapped'` in `unmatched_subjects` does not change future matching behavior, so a re-crawl will still classify the same raw course name as unmatched unless `GLOBAL_SUBJECT_MAPPING` or another persistent alias source is updated as part of the workflow.
2. [major] Acceptance criteria — the proposal says "align with NZQA official classification" but does not define a verifiable snapshot date, source artifact, or expected group/subject set, so the core requirement cannot be objectively tested or regression-checked.
3. [minor] Boundary conditions — raw-name normalization rules are undefined before `UNIQUE(school_number, raw_name)`, and frontend behavior for API errors or a fully empty response is not specified, which can create noisy review data and ambiguous UI behavior.
4. [question] For user — Should vocational pathway cards really include hardcoded "related subjects," and if yes, who is the business owner that approves those subject lists and bilingual descriptions?

### SCENARIOS_ASSESSMENT
- Scenario 1: WELL_DEFINED — user path, count logic, clickability, and zero-data handling are concrete.
- Scenario 2: NEEDS_WORK — the browsing experience is clear, but the proposal still lacks a measurable definition of complete NZQA alignment.
- Scenario 3: NEEDS_WORK — the display approach is simple, but the content source and approval rule for pathway-to-subject information are still unclear.
- Scenario 4: NEEDS_WORK — unmatched capture and review are covered, but the approved mapping result does not yet feed the matcher for future crawls.

### ARCHITECTURE_ASSESSMENT
- Fitness: 7
- Risks: review decisions for unmatched subjects are not persisted into reusable matching logic, NZQA alignment cannot be objectively validated, duplicate unmatched rows may accumulate without normalization, hardcoded pathway content may drift without a content owner
- Suggestions: make approved mappings update a persistent alias source used by crawlers, define a versioned NZQA snapshot/checklist for acceptance testing, normalize raw course names before deduplication and define empty/error states, confirm whether pathway cards should list related subjects at all and who approves that content

### SUMMARY
The proposal is close and appropriately simplified for the stated SQLite plus vanilla JS scope, but it is not fully approvable yet. The main remaining blocker is a real architecture gap in the unmatched review-to-backfill loop: reviewed mappings do not become future matching rules. After that, the biggest remaining requirement gap is testability of NZQA alignment, plus one user-side content decision around vocational pathway subject lists.
