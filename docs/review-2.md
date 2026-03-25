# Requirement Challenge — Round 2 of 5

**Model**: gpt-5.4-xhigh-fast
**Date**: 2026-03-25 21:54:55

---

我已拿到完整要求和固定输出模板，正在按其中的评审维度检查场景覆盖、歧义点和架构风险。### VERDICT: CHANGES_REQUESTED

### SCORE: 7

### COMPLETENESS
- Core table customization: COVERED — fixed school name column, default columns, column chooser, restore defaults, and localStorage restore are all specified.
- Sorting contract: GAP — the proposal does not fully lock the sortable column set or sort behavior; it makes some text columns non-sortable and assumes a numeric first-click direction without confirming that this matches the original requirement.
- Boundary and failure handling: PARTIAL — zero results, API failure, and corrupted/unknown localStorage values are covered, but storage write failure, hidden active sort state, and concurrent multi-tab preference changes are not.
- Architecture and data contract: PARTIAL — a LEFT JOIN on /api/schools is the right general approach, but the spec still relies on assumed one-to-one web data integrity and does not define response typing/formatting tightly enough for deterministic implementation.
- Testability: PARTIAL — several acceptance criteria remain subjective, especially around “real-time” updates and “smooth” mobile scrolling, so pass/fail testing is not fully measurable.
- Scope control: PARTIAL — the proposal is mostly within scope, but extra UX details such as grouped selector behavior and mobile bottom sheet should be clearly marked as implementation details so they do not expand acceptance scope.

### ISSUES
1. [critical] Requirement contract — The sorting contract is not fully aligned with the original requirement: the proposal makes tags and curriculum non-sortable and assumes first-click ascending for numeric columns without confirming that this is the intended product behavior. Lock the sortable columns and default direction before implementation.
2. [major] State behavior — The spec does not define what happens when the user hides the currently sorted column, changes visible columns while a sort is active, or sorts bilingual school names. This leaves the frontend state machine ambiguous and hard to verify.
3. [major] Boundary/performance — The architecture keeps client-side filtering and rendering, but it does not define behavior when the result set is not narrowed and the UI must render a wide table across 2,577 schools. Define whether the table is gated by filters, capped, or otherwise protected.
4. [minor] Testability/dependency handling — localStorage corruption is covered, but localStorage unavailability/write failure is not, and criteria like “real-time” and “smooth” are not measurable. Add explicit fallback behavior and concrete test thresholds.
5. [question] For user — Should composite text fields such as tags and curriculum be sortable to match the original “text columns sortable” expectation, and if yes, what business ordering should be used?

### SCENARIOS_ASSESSMENT
- [Scenario 1: first use / default browse]: NEEDS_WORK — default columns are clear, but behavior for broad or unfiltered result sets is still unspecified.
- [Scenario 2: customize columns]: NEEDS_WORK — persistence and null rendering are covered, but hiding a currently sorted column and storage write failure are not defined.
- [Scenario 3: sorting compare]: NEEDS_WORK — the scenario is partly described, but the sort rules are still incomplete and not fully consistent with the original requirement.
- [Scenario 4: mobile use]: NEEDS_WORK — sticky first column and horizontal scrolling are appropriate, yet the acceptance criteria are subjective and extreme-width cases are not specified.
- [Scenario 5: boundaries and errors]: NEEDS_WORK — it covers empty and API-failure states well, but misses storage denial, large-result rendering boundaries, and concurrent preference updates.

### ARCHITECTURE_ASSESSMENT
- Fitness: 7
- Risks: [sorting behavior may fail acceptance because the contract is not fully locked; hidden-column sort state is ambiguous; client-side rendering may degrade when results are not narrow; localStorage may be unavailable or fail on write; LEFT JOIN correctness depends on verified one-to-one school_web_data integrity]
- Suggestions: [define a per-column sorting matrix including first-click direction and sort key; specify what happens when a sorted column becomes hidden; define safe behavior for large or unfiltered result sets; add localStorage failure fallback rules; verify or enforce school_web_data.school_number uniqueness in schema/tests]

### SUMMARY
The proposal is close on the core mechanics and uses a sensible low-complexity architecture for the stated stack, but it is not yet production-ready because the sorting contract is still not fully pinned down, several UI state transitions remain undefined, and the large-result boundary is not specified. A tighter behavioral spec for sorting, hidden columns, storage fallback, and unfiltered rendering would make both implementation and acceptance testing much more reliable.
