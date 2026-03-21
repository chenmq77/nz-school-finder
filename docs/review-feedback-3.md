# Review Feedback — Round 3 (HTML version)

This document addresses **docs/review-3.md**.

**Date**: 2026-03-21
**Files**: index.html

---

## Issues Response

### Issue 1: .trim() on numeric API values crashes render
- **GPT said**: postal_code and isolation_index may be numeric from SQLite, calling .trim() throws TypeError.
- **Action**: FIXED
- **Solution**: Added `hasValue()` helper that safely handles any type (null/undefined/number/string). Replaced all `.trim()` on raw API values with `hasValue()` checks + `String(v).trim()`. Address/postal filters now use `hasValue()`. Isolation index uses `hasValue()` instead of direct `.trim()`.
- **Files changed**: index.html (hasValue helper, renderSectionB, renderSectionD)

### Issue 2: Blank boarding_facilities shown as "不提供寄宿"
- **GPT said**: Any non-"Yes" value including blank/unknown is mapped to "不提供寄宿", which is false information.
- **Action**: FIXED
- **Solution**: Added explicit 3-way branching: "Yes" → "提供寄宿", "No" → "不提供寄宿", anything else → "--".
- **Files changed**: index.html (renderSectionA boarding logic)

### Issue 3: innerHTML XSS from DB values
- **GPT said**: Raw DB values in onclick handlers, href attributes, and status text create XSS vectors.
- **Action**: FIXED
- **Solution**: (1) Search results rebuilt using DOM API (createElement + textContent + addEventListener) instead of innerHTML with inline onclick. School number sanitized to digits only. (2) Website URL validated with `isSafeUrl()` (only http/https allowed) and escaped with `esc()`. (3) Map link coordinates validated as numeric before constructing URL. (4) Tel/email href values escaped with `esc()`.
- **Files changed**: index.html (renderResults, renderSectionA website, renderSectionB tel/email, renderSectionD mapLink, isSafeUrl helper)

## Summary

- Fixed: 3 issues
- Rejected: 0 issues
- Out of scope: 0 issues
- Confidence: All type safety, data accuracy, and XSS issues resolved. DOM-based rendering for search results eliminates the primary injection vector.
