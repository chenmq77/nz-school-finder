# Requirement Challenge — Round 1 of 5

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-25 21:48:36

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 6

### COMPLETENESS
- Core table interactions: PARTIAL — default columns, column toggling, persistence, and sortable headers are covered at happy-path level, but reset behavior and missing-data handling are not fully defined.
- Field coverage: GAP — ethnicity composition is missing entirely from the proposed column set, and the fixed school name column does not specify how Chinese and English names are rendered.
- Boundary and failure handling: GAP — there is no defined behavior for zero results, API failure, malformed `localStorage`, stale saved column keys, or unavailable web data during sorting.
- Architecture alignment: PARTIAL — the `LEFT JOIN` approach fits the need to surface web fields, but the proposal also introduces `logo_url` and assumes full client-side filtering, which are not required by the brief.
- Acceptance criteria: PARTIAL — some scenarios have acceptance notes, but they are not concrete enough for mobile behavior, performance, and sort behavior across null/composite values.

### ISSUES
1. [critical] Requirement coverage — The configurable column model omits ethnicity composition and does not define the fixed bilingual school name presentation, so the proposed UI does not fully cover the stated available fields.
2. [major] Sorting behavior — The proposal says text sorts A-Z and numeric sorts asc/desc, but it does not define how `—`/null values sort, how composite fields like tags or curriculum sort, or whether sorting is stable after filters change.
3. [major] Boundary conditions — No scenario covers zero matching schools, `/api/schools` failure, malformed or blocked `localStorage`, or saved preferences containing removed/unknown column keys.
4. [major] Architecture fit — The plan assumes all 2577 schools are returned and filtered on the client, which is a material behavior change not requested in the brief and may create unnecessary payload/render costs.
5. [major] API contract — The `LEFT JOIN` design does not state whether `school_web_data` is guaranteed one row per school or define exact field types/null semantics, which risks duplicate rows or inconsistent frontend formatting.
6. [minor] Scope control — Adding `logo_url` expands the API and UI surface without a stated user need, which is scope creep for this requirement.
7. [minor] UX completeness — The column selector has no defined reset-to-default action, no rule for hiding all optional columns, and no mobile-specific behavior for opening/closing the checkbox panel.
8. [question] For user — Should ethnicity composition appear as seven separate configurable columns, one aggregated column, or be explicitly deferred from v1 for readability and density reasons?

### SCENARIOS_ASSESSMENT
- First use / default browse: NEEDS_WORK — the default 5 columns are defined, but initial sort state and bilingual name rendering are still ambiguous.
- Customize columns: NEEDS_WORK — the happy path is covered, but invalid saved preferences, reset behavior, and the missing ethnicity field strategy are not.
- Sorting comparison: NEEDS_WORK — numeric vs text sorting is stated, but null ordering, composite sort keys, and sparse web-data behavior are undefined.
- Mobile usage: NEEDS_WORK — sticky first column and horizontal scroll are directionally correct, but the column-picker interaction on small screens is not specified.
- Empty/error recovery: MISSING — there is no user scenario for zero results, API failure, or storage recovery.
- Sparse web-data comparison: MISSING — only 18 schools have web data, but the proposal does not define how users should interpret or sort columns where most rows are blank.

### ARCHITECTURE_ASSESSMENT
- Fitness: 6
- Risks: [required fields are not fully represented; null-heavy web-data columns can make sorting misleading; `LEFT JOIN` row cardinality is assumed but not defined; client-side full-dataset filtering may add avoidable payload/render cost; saved column preferences can break after schema changes]
- Suggestions: [define the full column catalog including ethnicity and bilingual name rendering; specify sort rules for null, blank, and composite values; document API field types, null semantics, and one-row-per-school join guarantees; keep current filtering behavior unless a deliberate change is approved; add reset/versioning/fallback logic for `localStorage`; remove `logo_url` unless the user explicitly wants it]

### SUMMARY
The proposal is a solid first-pass skeleton, but it is not yet complete enough to implement safely as written. The main problems are missing required field coverage, undefined behavior for null-heavy/sparse web data, missing empty and failure scenarios, and an architectural drift toward client-side full-dataset filtering that is not justified by the requirement. It needs a tighter product decision on ethnicity presentation plus a more explicit API and sorting contract before it is production-ready.
