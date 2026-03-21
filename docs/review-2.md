# Review Round 2 of 20

**Model**: gpt-5.4-xhigh-fast
**Files**: index.html,server.py
**Date**: 2026-03-21 21:42:57

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 7

### REQUIREMENT_COVERAGE
- Search by school English name and show the selected school's information: PARTIAL — the basic search/detail flow exists, but async responses are not sequenced, so stale search results or the wrong school detail can overwrite the latest user action.
- Five-category V2 layout and interaction model: MET — the UI follows the required A→E parent-decision order, keeps A/B/C expanded by default, and makes D/E collapsible.
- Coverage of all 49 CSV fields and required presentation emphasis: PARTIAL — the implementation renders all listed fields and includes the required merged address/community rows, clickable contact links, ethnic bars, international-student emphasis, and EQI interpretation, but `Total School Roll` is shown as `--` instead of `0` for legitimate zero-roll schools.
- Previous round 1 fixes: MET — `loadSchool()` now checks `res.ok`, `showDetailError()` preserves the detail shell/back button while hiding B-E, unknown GET routes return 404, and the search API/frontend now return and display a separate total count.

### ISSUES
1. [major] index.html:505, index.html:552 — `doSearch()` and `loadSchool()` do not guard against out-of-order async responses, so an older slower request can overwrite a newer query or school selection and leave the UI showing stale results or the wrong school. Suggested fix: use `AbortController` or a monotonically increasing request token for both flows, and ignore responses that are no longer the latest request.
2. [minor] index.html:543 — `loadSchool()` shows the detail pane before clearing previous content or rendering a loading state, so switching between schools briefly displays the last school's data under the new interaction. Suggested fix: clear `bodyA`-`bodyE` or render a loading placeholder before revealing the detail pane, or only show the pane after fresh data is ready.
3. [minor] index.html:655 — `Total School Roll` is rendered as `--` whenever the parsed value is `0`, which misstates valid zero-roll schools such as `New`, `Proposed`, or `Not Yet Open` records. Suggested fix: distinguish missing/invalid values from numeric zero and render `0` explicitly.

### SUMMARY
The implementation is close: the V2 five-section structure, 49-field coverage, and round-1 fixes are largely in place, and the overall organization matches the requirement well. Approval is still blocked by the async correctness bug that can show stale results or the wrong school after rapid user interactions, plus two smaller display-accuracy issues around transient stale detail content and zero-roll schools.
