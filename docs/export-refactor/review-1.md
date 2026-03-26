# Review Round 1 of 3

**Model**: gpt-5.4-xhigh-fast
**Files**: /tmp/export-code.js
**Date**: 2026-03-26 17:26:09

---

### VERDICT: CHANGES_REQUESTED

### SCORE: 6

### REQUIREMENT_COVERAGE
- No duplicated html2canvas/download code: MET — both table and FAQ exports now route the render/download flow through `exportDivAsImage()`.
- Error handling (no html2canvas, null blob) in shared utility: MET — missing `html2canvas`, null blob, and render failures are handled inside the shared utility.
- Loading state management via loadingBtn parameter: PARTIAL — the shared utility accepts `loadingBtn`, but `canvas.toBlob()` is not awaited so the button is reset before export completion, and `exportFaqAsImage()` does not pass a loading button at all.
- iOS fallback (window.open) in shared utility: MET — the iOS fallback is implemented inside `exportDivAsImage()`.
- DOM cleanup in finally block: MET — the temporary export DOM is removed in `finally`.
- Toast notifications for errors: MET — the error paths call `showToast()`.
- All export text follows i18n via t(): NOT_MET — several export-facing strings are still hardcoded instead of going through `t()`.

### ISSUES
1. [major] /tmp/export-code.js:157 — `exportDivAsImage()` finishes before `canvas.toBlob()` completes, so the loading button is restored too early; `exportFaqAsImage()` also calls the shared utility without a `loadingBtn`, so FAQ export has no loading-state protection at all — suggested fix: wrap `canvas.toBlob()` in a Promise, await it before leaving `exportDivAsImage()`, and pass the triggering FAQ button into the shared utility.
2. [major] /tmp/export-code.js:28 — export text is still hardcoded in multiple places (`Low-High`, `High-Low`, `by`, `Y`, `NZ School Finder`, `/w`) instead of using `t()`, which directly violates requirement 7 — suggested fix: move every export-facing string/token into i18n keys and build summaries/labels only from translated templates.
3. [major] /tmp/export-code.js:36 — the requested refactored structure is incomplete: `buildExportTemplate()` still builds its own footer instead of reusing `buildExportFooter()`, and `exportFaqAsImage()` still clones live FAQ DOM instead of building FAQ export content through dedicated helpers (`buildEqiBandBar()` / `buildEqiFaqHtml()`) — suggested fix: complete the refactor so both export paths are composed from the shared footer and dedicated FAQ builder helpers.
4. [minor] /tmp/export-code.js:210 — `exportFaqAsImage()` assumes `.faq-q span` and `.faq-a` always exist; a small FAQ markup change will throw before any graceful failure path runs — suggested fix: null-check the queried nodes and return through the shared error handling path.

### SUMMARY
The shared `exportDivAsImage()` extraction is a solid first step, but this refactor does not fully meet the stated requirement set yet. The main blockers are incomplete loading-state handling, missing i18n coverage for export text, and an unfinished structural refactor around the shared footer/FAQ builders, so this should not be approved as-is.
