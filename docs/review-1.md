# Review Round 1 of 20

**Model**: gpt-5.4-xhigh-fast
**Files**: index.html,server.py
**Date**: 2026-03-21 21:35:37

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 6

### REQUIREMENT_COVERAGE
- Core flow ("user enters an English school name -> system matches data -> structured display"): PARTIAL — the happy path works, but broad searches are silently capped and non-2xx detail responses are rendered incorrectly instead of showing a recoverable error state.
- Five-category V2 layout aligned to the parent/student decision flow: MET — the UI is split into A-E and the grouping of identity, contact, student profile, quality/features, and administration matches the requirement.
- Coverage of all 49 CSV fields across A-E: MET — sections A-E reference every listed field, including combined address/postal fields, coordinates, and SA2/community fields.
- Default expansion/collapse behavior: MET — A/B/C are expanded by default, while D/E are collapsible and initially collapsed.
- Required visuals and bilingual presentation: MET — ethnic distribution bar charts, international-student highlighting, EQI interpretation, and bilingual labels are implemented.

### ISSUES
1. [major] index.html:552 — `loadSchool()` never checks `res.ok`, so a 404/500 JSON payload from `/api/school/<num>` is treated as a valid school object and rendered as a mostly blank profile instead of an error state. Suggested fix: throw on non-2xx responses before calling `renderSchool()`.
2. [major] index.html:556 — the fetch-failure path replaces the entire `#schoolDetail` container with a single error div, which removes the back button and section bodies and leaves the page unable to recover without a full refresh. Suggested fix: keep the detail scaffold intact and render errors inside a dedicated message area.
3. [major] server.py:75 — falling through to `super().do_GET()` exposes arbitrary files from the working directory, including `schools.db` and source files, which is unnecessary for this app and expands the attack surface. Suggested fix: return 404 for unknown routes or serve only an explicit safe static directory.
4. [minor] server.py:37 — search results are hard-capped at 50 while the UI reports `count` as if it were the full match count, so broad fuzzy queries can hide valid schools and mislead users. Suggested fix: remove the hard cap for this small dataset, or return a real total count plus pagination/capped-results messaging.

### SUMMARY
This is a strong first-round implementation of the V2 information architecture: the five-section layout, field mapping, expansion behavior, and key visual elements all line up well with the requirement. However, it is not ready for approval yet because the detail-loading flow fails badly on backend errors and the server still exposes unintended files; those issues should be fixed before the next review round.
