# Review Round 3 of 20

**Model**: gpt-5.4-xhigh-fast
**Files**: index.html,server.py
**Date**: 2026-03-21 21:49:21

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 7

### REQUIREMENT_COVERAGE
- [User inputs an English school name and the system matches it from the CSV]: MET — the UI/search API support direct name-based fuzzy matching on `school_name`, and the round-2 abort handling prevents stale search results.
- [A. School Identity Overview (7 fields, default expanded)]: PARTIAL — all 7 required fields are present and section A is open by default, but blank `boarding_facilities` values are rendered as "not boarding" instead of unknown.
- [B. Location & Contact (10 fields, default expanded)]: PARTIAL — all required fields are displayed with the intended address merging, but the render path assumes string types for `postal_code` and can fail on valid numeric API values.
- [C. Student Size & Composition (9 fields, default expanded, ethnicity visualization, international highlighted)]: MET — total roll, all 6 ethnicity fields, international students, and enrolment scheme are all rendered with the expected emphasis, and the null-vs-0 fix is correctly implemented here.
- [D. School Quality & Features (11 fields, click to expand, EQI interpretation)]: PARTIAL — all 11 required fields are represented and the section is collapsible, but the `isolation_index` handling can break or misclassify valid numeric values.
- [E. Administrative & Regional Attribution (12 fields, click to expand)]: MET — all 12 required fields are represented, and combining SA2 name/code matches the provided example style.
- [All 49 CSV columns are covered under the 5 parent-centric categories]: MET — every required field from A1-E12 is present in the UI.
- [V2 interaction model (A/B/C open by default, D/E click-to-expand)]: MET — the DOM structure and reset logic match the required interaction pattern.
- [Round 2 feedback fixes]: MET — both fetch flows now abort previous requests, old detail content is cleared before fresh data renders, and detail total roll distinguishes blank from numeric `0`.

### ISSUES
1. [major] index.html:630,709 — `renderSectionB()` and `renderSectionD()` call `.trim()` on raw API values (`postal_code`, `isolation_index`). If SQLite returns these as numbers, the detail render throws `TypeError`, and numeric `0` isolation values are also treated as missing. — Suggested fix: add a shared helper such as `hasValue(v) { return v !== null && v !== undefined && String(v).trim() !== ''; }` and only call `String(v).trim()` after that check.
2. [major] index.html:605 — `renderSectionA()` maps every non-`Yes` boarding value, including blank/unknown data, to `不提供寄宿`, which can show false information for one of the highest-priority parent-facing fields. — Suggested fix: use explicit `Yes` / `No` / unknown branching and render `--` for missing values instead of treating them as `No`.
3. [major] index.html:538,608,634,725,748 — database-backed values are interpolated directly into `innerHTML` attribute/handler contexts (`onclick`, `href`, map link, and fallback status text). A malformed or poisoned CSV row can break markup or enable XSS in the browser. — Suggested fix: stop constructing these parts with raw HTML strings; create DOM nodes, assign `textContent`, validate allowed URL schemes/characters before setting `href`, and replace inline `onclick` with `addEventListener`.

### SUMMARY
This round is much closer: the V2 information architecture is implemented correctly, all 49 required fields are represented, the default-expand/click-expand behavior matches the requirement, and the round-2 stale-request/stale-content fixes appear valid. However, I cannot approve it yet because there are still major correctness and security problems in the rendering layer: valid numeric API values can break sections B/D, missing boarding data is converted into a false negative in a core decision field, and several DB values are still injected into HTML unsafely.
