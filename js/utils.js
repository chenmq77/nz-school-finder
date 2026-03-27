/**
 * Shared utility functions — extracted from index.html
 * Pure functions with no side effects or global state dependencies.
 */

/** HTML-escape a string to prevent XSS */
export function esc(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

/** Return '--' for null/undefined/empty values */
export function safe(v) {
  if (v === null || v === undefined) return '--';
  const s = String(v).trim();
  return s !== '' ? s : '--';
}

/** Check if a value is non-null, non-undefined, non-empty */
export function hasValue(v) {
  return v !== null && v !== undefined && String(v).trim() !== '';
}

/** Ensure URL has http(s) prefix */
export function ensureHttp(url) {
  if (!url || url === '--') return '#';
  return url.startsWith('http') ? url : 'http://' + url;
}

/** Validate and sanitize a URL for safe use in href */
export function safeUrl(url) {
  if (!url) return '#';
  try {
    const u = new URL(url, window.location.origin);
    if (u.protocol === 'http:' || u.protocol === 'https:') return u.href;
  } catch (e) { /* invalid URL */ }
  return '#';
}

/** Show a temporary toast notification */
export function showToast(msg, duration = 3000) {
  const toast = document.createElement('div');
  toast.style.cssText = 'position:fixed;top:20px;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:10px 20px;border-radius:8px;font-size:14px;z-index:9999;transition:opacity 0.3s;';
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, duration);
}
