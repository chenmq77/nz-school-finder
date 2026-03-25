# Requirement Challenge — Round 3 of 5

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-26 02:19:08

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 7

### COMPLETENESS
- [core configurable table flow]: COVERED — default columns, column chooser, persistence, sorting interactions, and mobile horizontal scrolling are all defined at a usable level.
- [field catalog alignment]: PARTIAL — the requirement lists seven ethnicity source fields, but the proposal only exposes five sub-columns and the stated total of 19 columns does not match the actual definitions.
- [sorting behavior]: PARTIAL — click cycle, null placement, and per-column defaults are defined, but bilingual name sorting and the business meaning of the default EQI direction are still ambiguous.
- [error and degraded states]: COVERED — zero results, API failure, invalid localStorage data, and localStorage write failure are explicitly handled.
- [testability]: PARTIAL — most acceptance criteria are measurable, but sorting cannot be fully verified until the spec defines whether the 100-row cap is applied before or after sorting.

### ISSUES
1. [critical] Sorting/Data Window — The proposal says the unfiltered view shows only the first 100 schools, but it does not define whether sorting operates on all 2577 schools and then displays the top 100, or sorts only the visible 100. That changes the meaning of comparison results and must be specified.
2. [major] Data Model Completeness — The available data includes `MELAA` and `Other` ethnicity fields, but the column model omits them while also claiming there are 19 columns. The schema, UI column registry, and requirement inventory are not fully aligned.
3. [minor] Sorting Semantics — `name` sorting is defined as `school_name_cn` fallback `school_name`, which does not clearly satisfy the stated "A-Z" rule for text columns, and `eqi` assumes "low = good" without business confirmation. These rules are likely to confuse users unless explicitly justified.
4. [question] For user — Do you want the product to expose all available ethnicity fields, and what should be the canonical sort rule for the bilingual school name column and EQI default direction from a business perspective?

### SCENARIOS_ASSESSMENT
- [scenario 1: first-use default browsing]: NEEDS_WORK — the initial default view is clear, but the interaction between the 100-row cap and sorting is not.
- [scenario 2: custom columns]: WELL_DEFINED — grouping, persistence, restore-default behavior, and invalid localStorage recovery are all adequately specified.
- [scenario 3: sorting]: NEEDS_WORK — the mechanical click behavior is clear, but the sort scope and some domain-specific sort rules are still underspecified.
- [scenario 4: mobile]: WELL_DEFINED — sticky name column, horizontal scrolling, and a mobile-specific selector pattern are sufficient for implementation.
- [scenario 5: edge and error states]: WELL_DEFINED — the main failure and empty-state paths are covered with expected UI behavior.

### ARCHITECTURE_ASSESSMENT
- Fitness: 7/10
- Risks: ambiguity between display cap and sort scope; incomplete ethnicity column mapping; unconfirmed business semantics for bilingual name sorting and EQI ordering
- Suggestions: define whether the 100-row limit is fetch-time or display-time and how sorting interacts with it; align the column registry with the full available field set or explicitly de-scope omitted fields; get a business decision on canonical name sorting and EQI default order before implementation

### SUMMARY
The proposal is close and the main user flows are now largely covered, but it is not yet approval-ready because one core correctness issue remains unresolved: how sorting behaves when the unfiltered view is capped at 100 rows. In addition, the column inventory is internally inconsistent and the sort semantics for bilingual names and EQI still rely on assumptions rather than explicit business rules.
