/**
 * API module — unified fetch wrapper with error handling and abort support.
 * Extracted from index.html to centralize all API calls.
 */

const BASE = '';  // relative to current origin

/** Active AbortControllers by request key */
const _controllers = {};

/**
 * Cancel any in-flight request for the given key.
 * Call this before making a new request to the same endpoint group.
 */
function abort(key) {
  if (_controllers[key]) {
    _controllers[key].abort();
    delete _controllers[key];
  }
}

/**
 * Core fetch wrapper with:
 * - AbortController keyed by request group
 * - Auto JSON parsing
 * - Timeout (default 15s)
 * - Graceful error handling (returns null on failure)
 *
 * @param {string} path - API path (e.g. '/api/schools?limit=20')
 * @param {object} opts
 * @param {string} opts.key - abort group key (e.g. 'search', 'detail')
 * @param {number} opts.timeout - ms, default 15000
 * @returns {Promise<object|null>} parsed JSON or null on error
 */
export async function apiFetch(path, { key = null, timeout = 15000 } = {}) {
  // Cancel previous request in same group
  if (key) abort(key);

  const controller = new AbortController();
  if (key) _controllers[key] = controller;

  // Timeout
  const timer = setTimeout(() => controller.abort(), timeout);

  try {
    const res = await fetch(`${BASE}${path}`, { signal: controller.signal });
    clearTimeout(timer);
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    clearTimeout(timer);
    if (err.name === 'AbortError') return null;  // cancelled or timeout
    console.warn(`API error [${path}]:`, err.message);
    return null;
  } finally {
    if (key) delete _controllers[key];
  }
}

/**
 * Fetch multiple API paths in parallel, all under the same abort key.
 * Returns array of results (null for failed requests).
 *
 * @param {string[]} paths - array of API paths
 * @param {string} key - shared abort key
 * @returns {Promise<(object|null)[]>}
 */
export async function apiFetchAll(paths, key) {
  if (key) abort(key);

  const controller = new AbortController();
  if (key) _controllers[key] = controller;

  const timer = setTimeout(() => controller.abort(), 20000);

  try {
    const results = await Promise.all(
      paths.map(async (path) => {
        try {
          const res = await fetch(`${BASE}${path}`, { signal: controller.signal });
          if (!res.ok) return null;
          return await res.json();
        } catch (err) {
          if (err.name === 'AbortError') return null;
          return null;
        }
      })
    );
    clearTimeout(timer);
    return results;
  } catch (err) {
    clearTimeout(timer);
    return paths.map(() => null);
  } finally {
    if (key) delete _controllers[key];
  }
}

// ── Convenience wrappers ──

/** Search schools by keyword */
export function searchSchools(q) {
  return apiFetch(`/api/search?q=${encodeURIComponent(q)}`, { key: 'search' });
}

/** Get filtered school list */
export function fetchSchools(params) {
  return apiFetch(`/api/schools?${params.toString()}`, { key: 'list' });
}

/** Get single school detail */
export function fetchSchool(num) {
  return apiFetch(`/api/school/${num}`, { key: 'detail' });
}

/** Get school web data (crawled) */
export function fetchSchoolWeb(num) {
  return apiFetch(`/api/school/${num}/web`, { key: 'web' });
}

/** Get school performance + NCEA data in parallel */
export function fetchSchoolNceaAll(num) {
  return apiFetchAll([
    `/api/school/${num}/performance`,
    `/api/school/${num}/ncea`,
  ], 'ncea');
}

/** Get dashboard stats */
export function fetchStats() {
  return apiFetch('/api/stats', { key: 'stats' });
}

/** Cancel all in-flight requests */
export function abortAll() {
  Object.keys(_controllers).forEach(abort);
}
