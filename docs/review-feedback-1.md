# Review Feedback — Round 1 (HTML version)

This document addresses **docs/review-1.md**.

**Date**: 2026-03-21
**Files**: index.html, server.py

---

## Issues Response

### Issue 1: loadSchool() never checks res.ok
- **GPT said**: Non-2xx responses are treated as valid school data and rendered as blank profile.
- **Action**: FIXED
- **Solution**: Added `res.ok` check before parsing. Non-2xx returns show error via `showDetailError()`. Also checks for `s.error` in JSON response.
- **Files changed**: index.html:551-558

### Issue 2: Fetch failure destroys detail DOM structure
- **GPT said**: Replacing `$detail.innerHTML` removes back button and section bodies, page can't recover.
- **Action**: FIXED
- **Solution**: Created `showDetailError()` function that shows error inside section A body only, hides sections B-E, preserves back button. `renderSchool()` restores section visibility when loading successfully.
- **Files changed**: index.html:762-775, index.html:563

### Issue 3: super().do_GET() exposes arbitrary files
- **GPT said**: Falling through to SimpleHTTPRequestHandler serves any file from working directory.
- **Action**: FIXED
- **Solution**: Replaced `super().do_GET()` with `self.send_error(404, "Not Found")` for unknown routes.
- **Files changed**: server.py:75-76

### Issue 4: Search count misleading with hard cap
- **GPT said**: Count shows capped results as if they were the total, hiding valid matches.
- **Action**: FIXED
- **Solution**: Added separate COUNT query for real total. API now returns `{results, count, total}`. Frontend shows "找到 N 所学校（显示前 50 所）" when results are capped.
- **Files changed**: server.py:27-45, server.py:56, index.html:519,523

## Summary

- Fixed: 4 issues
- Rejected: 0 issues
- Out of scope: 0 issues
- Confidence: All security, error handling, and UX issues resolved.
