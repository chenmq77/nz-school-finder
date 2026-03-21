# Review Feedback — Round 2 (HTML version)

This document addresses **docs/review-2.md**.

**Date**: 2026-03-21
**Files**: index.html

---

## Issues Response

### Issue 1: Async race condition in doSearch() and loadSchool()
- **GPT said**: Older slower requests can overwrite newer results, showing stale data.
- **Action**: FIXED
- **Solution**: Added `AbortController` for both search and detail flows. Each new request aborts the previous one. `AbortError` is caught and silently ignored since it means the request was superseded.
- **Files changed**: index.html (searchController/detailController state vars, doSearch(), loadSchool())

### Issue 2: Switching schools briefly shows old school data
- **GPT said**: Detail pane shows before clearing previous content.
- **Action**: FIXED
- **Solution**: `loadSchool()` now immediately clears all section bodies, shows a loading spinner in section A, and hides sections B-E. Content is only revealed after the new data arrives and `renderSchool()` restores section visibility.
- **Files changed**: index.html (loadSchool())

### Issue 3: Total School Roll shows "--" for valid zero-roll schools
- **GPT said**: Schools with status New/Proposed/Not Yet Open may have 0 students, should show "0" not "--".
- **Action**: FIXED
- **Solution**: Changed `total` parsing to distinguish missing/blank values (→ null → "--") from numeric zero (→ 0 → "0"). Uses explicit null check instead of falsy check.
- **Files changed**: index.html (renderSectionC total display)

## Summary

- Fixed: 3 issues
- Rejected: 0 issues
- Out of scope: 0 issues
- Confidence: All async safety, loading state, and data accuracy issues resolved.
