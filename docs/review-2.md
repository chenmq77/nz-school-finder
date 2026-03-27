# Requirement Challenge — Round 2 of 20

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-27 13:36:36

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 6

### COMPLETENESS
- [Core browse-and-click flow]: COVERED — The parent journey from overview tree to filtered school list is defined, and `school_count` is explicitly based on `COUNT(DISTINCT school_number)`.
- [NZQA taxonomy alignment]: PARTIAL — The two-level structure is modeled, but the proposal does not define how junior courses, composite school-defined courses, or non-NZQA labels are treated.
- [Crawler matching and review loop]: PARTIAL — Unmatched capture exists, but fuzzy-match rules, reviewer decision criteria, and the closed-loop backfill process are not defined.
- [Vocational Pathways behavior]: PARTIAL — The display is specified, but the proposal adds a strong subject linkage that is still semantically unclear against the “independent dimension” requirement.
- [Migration and data integrity]: GAP — There is no concrete plan for reconciling existing `school_subjects` data, preventing duplicate school-subject rows, or safely transitioning current 14-school data to the new taxonomy.
- [Partial coverage communication]: GAP — The proposal says “no special handling,” but it does not define how to prevent users from misreading counts as full-market coverage while only a subset of schools is indexed.

### ISSUES
1. [critical] Scope boundary — The proposal never defines whether junior courses, school-specific composite courses, or marketing labels should be excluded, mapped to NZQA subjects, or split across multiple subjects — without this boundary, taxonomy alignment and school counts are not reliable.
2. [critical] Data workflow — Manual review stops at `unmatched_subjects`, but there is no closed-loop process to reprocess skipped records and backfill `school_subjects` after a mapping decision — the core “store then periodically review” requirement is not operational yet.
3. [major] Partial-data UX — Showing `N schools` without an explicit indexed-school denominator and last-updated context can still mislead users while coverage is only 14 schools and expanding — greyed-out zero counts do not solve this for nonzero counts.
4. [major] Architecture fit — `subject_pathway` introduces a strong many-to-many coupling between pathways and subjects even though the requirement describes pathways as an independent dimension — this may be unnecessary scope growth unless explicitly confirmed.
5. [major] Data model — `UNIQUE(school_number, raw_name)` plus `INSERT OR IGNORE` loses recurrence and freshness information for persistent unmatched rows — reviewers cannot see whether an issue is still active, frequent, or already fading.
6. [major] Testability — Fuzzy-match thresholds, normalization rules, precedence between synonym mapping and fuzzy match, and false-positive safeguards are undefined — acceptance cannot be measured objectively.
7. [minor] Frontend/API behavior — Empty states, API failure behavior, ordering of groups/subjects, and Chinese fallback behavior when `name_cn` is missing are not specified.
8. [question] For user — Should vocational pathways remain informational cards only, or do you explicitly want them to drive subject-to-school navigation through a curated `subject_pathway` mapping?
9. [question] For user — Should the overview represent only strict NZQA/NCEA subjects, or should junior/composite school course names also be surfaced through mapping rules for better discoverability?

### SCENARIOS_ASSESSMENT
- [scenario 1]: NEEDS_WORK — The drill-down is clear, but the meaning of the count is still ambiguous because the indexed-school coverage is not surfaced.
- [scenario 2]: NEEDS_WORK — The taxonomy tree is defined, but the handling of non-NZQA or school-specific course names is missing, which weakens the promise of “official” alignment.
- [scenario 3]: NEEDS_WORK — The UI is clear, but the business meaning and source of pathway-to-subject mappings are still unclear and may conflict with the original independence requirement.
- [scenario 4]: NEEDS_WORK — Capturing unmatched courses is covered, but status semantics and the post-review reprocessing workflow are incomplete.
- [scenario 5]: NEEDS_WORK — “No special handling” is too weak as an acceptance definition because it does not prevent misleading interpretation of partial coverage.

### ARCHITECTURE_ASSESSMENT
- Fitness: 6/10
- Risks: Undefined inclusion boundary for real-world course names, no closed-loop remap/backfill process, misleading subject counts under partial coverage, unnecessary coupling via `subject_pathway`, loss of unmatched recurrence/freshness data, and ambiguous fuzzy-matching behavior.
- Suggestions: Define strict inclusion/exclusion rules for non-NZQA and composite course names; add a review-to-reprocess workflow for unmatched items; expose coverage metadata such as indexed school count and last updated date; confirm whether pathway-to-subject mapping is truly in scope before keeping `subject_pathway`; add audit fields such as `first_seen_at`, `last_seen_at`, `occurrence_count`, `match_type`, or `confidence`; specify frontend/API error, empty, sorting, and bilingual fallback behavior.

### SUMMARY
The proposal is directionally solid and much more concrete than a raw requirement, but it is not approval-ready because the most important operational boundaries are still unresolved: what exactly counts as an NZQA-aligned subject in messy school data, how manual review actually feeds corrected data back into production counts, and how the UI avoids overstating coverage while only a subset of schools is indexed. Resolve those points and explicitly confirm the intended role of vocational pathways, and the design will be much closer to a sound, testable implementation.
