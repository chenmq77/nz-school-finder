# Requirement Challenge — Round 6 of 8

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-27 11:40:16

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 8

### COMPLETENESS
- Core summary ingestion: COVERED — checksum validation, transactional re-import, school matching flow, and golden-data assertions are defined.
- Subject ranking ingestion: PARTIAL — extraction is in scope, but there is no explicit completeness check that every expected subject block and ranking row was captured.
- UI/API behavior: COVERED — the list UE column, detail-section visibility, and endpoint shapes are clear enough for Release 1.
- Boundary and error handling: PARTIAL — unmatched core schools fail fast, but ranking-page mismatches and missing/suppressed values still have undefined handling.
- Scope alignment: PARTIAL — Release 1 is intentionally narrow, but deferring compare-page integration still needs explicit business confirmation against the original goal.

### ISSUES
1. [major] Validation coverage — Subject rankings do not have a row-count or completeness assertion, so losing a whole subject block or part of a page could still pass validation if the remaining rows look valid — add expected subject-set and per-subject row-count checks, ideally pinned to the PDF checksum.
2. [major] Data integrity — Unmatched Top 10 schools are always skipped, which makes an intentional “outside schools table” skip indistinguishable from a real matching/parser regression for a school that should map — keep a skip report and fail unless each skipped ranking name is on an explicit approved allowlist.
3. [minor] Data semantics — The proposal does not define how blanks, dashes, or suppressed PDF values are stored and rendered, so `NULL`, `0`, and “not reported” can be conflated in validation, API payloads, and UI output — add field-level null-handling rules.
4. [question] For user — The original business goal is to strengthen school comparison, but Release 1 excludes the compare page; is list + detail enough for launch, or must comparison views consume NCEA data in this release?

### SCENARIOS_ASSESSMENT
- Scenario 1: NEEDS_WORK — The core import path is solid, but subject-ranking completeness and unexpected ranking-name skips are not yet protected.
- Scenario 2: WELL_DEFINED — UE display, no-data fallback, and sorting behavior are concrete and implementable.
- Scenario 3: NEEDS_WORK — The main detail-section behavior is defined, but the spec should clarify how “not ranked” and “not reported” are represented to users.

### ARCHITECTURE_ASSESSMENT
- Fitness: 8/10
- Risks: subject-ranking data can be partially lost without failing the import; ranking-name mismatches can be silently converted into skips; blank/suppressed PDF values may be interpreted inconsistently across DB, API, and UI
- Suggestions: add completeness assertions for subject rankings; distinguish expected ranking skips from unexpected matching failures; define field-level NULL parsing/rendering rules and label subject rankings as Top 10-only where shown

### SUMMARY
The proposal is close to approval: the Release 1 scope is disciplined, the storage model is lean, and the core summary import path now has good safety rails. The remaining issues are concentrated in subject-ranking correctness and missing-value semantics, plus one open product decision about whether compare-page integration can wait; once those are tightened, the spec is production-ready.
