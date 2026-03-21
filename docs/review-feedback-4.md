# Review Feedback — Round 4 (HTML version)

This document addresses **docs/review-4.md**.

**Date**: 2026-03-21
**Files**: index.html

---

## Issues Response

### Issue 1: Unescaped status fallback value in innerHTML
- **GPT said**: When status is not in statusMap, the raw API value is injected into innerHTML without escaping, leaving a stored-XSS path.
- **Action**: FIXED
- **Solution**: Applied `esc()` to both `statusText` and `statusClass` in the innerHTML template. Any unexpected status value from the DB/API is now HTML-escaped before rendering.
- **Files changed**: index.html:771

## Summary

- Fixed: 1 issue
- Rejected: 0 issues
- Out of scope: 0 issues
- Confidence: The last XSS vector is now closed. All DB-sourced values in the rendering layer are either escaped via `esc()`, constructed with DOM APIs, or validated before use.
