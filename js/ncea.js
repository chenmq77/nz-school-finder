/**
 * NCEA module — Metro honours panel + performance data loading.
 * Extracted from index.html.
 *
 * Depends on globals: _lang, t(), esc(), TRANSLATIONS
 * Depends on renderPerformanceHtml() still in index.html (too large to extract now)
 */

// ── State ──

let _cachedPerformance = null;
let _cachedNcea = null;

export function getCachedPerformance() { return _cachedPerformance; }
export function getCachedNcea() { return _cachedNcea; }

// ── Load NCEA + Performance Data ──

export async function loadPerformanceData(schoolNum) {
  document.getElementById('sectionH').style.display = 'none';
  document.getElementById('bodyH').innerHTML = '';
  _cachedNcea = null;
  _cachedPerformance = null;
  try {
    const [perfRes, nceaRes] = await Promise.all([
      fetch(`/api/school/${schoolNum}/performance`),
      fetch(`/api/school/${schoolNum}/ncea`),
    ]);
    let perfData = null, nceaData = null;
    if (perfRes.ok) { const d = await perfRes.json(); if (d && d.performance) perfData = d; }
    if (nceaRes.ok) { const d = await nceaRes.json(); if (d && d.ncea_summary) nceaData = d; }
    _cachedPerformance = perfData;
    _cachedNcea = nceaData;
    if (!perfData && !nceaData) return;
    let html = '';
    if (perfData) html += renderPerformanceHtml(perfData);
    if (nceaData) html += renderMetroNcea(nceaData);
    if (!html) return;
    document.getElementById('sectionH').style.display = '';
    document.getElementById('bodyH').innerHTML = html;
  } catch (e) { /* silently ignore */ }
}

// ── Subject Name Translations ──

const SUBJECT_CN = {
  'Engineering and Manufacturing': '\u5de5\u7a0b\u4e0e\u5236\u9020\u5b66\u79d1',
  'Field M\u0101ori': '\u6bdb\u5229\u6587\u5316\u5b66\u79d1',
  'Health and Physical Education': '\u5065\u5eb7\u4e0e\u4f53\u80b2\u5b66\u79d1',
  'English and Communication Skills': '\u82f1\u8bed\u4e0e\u6c9f\u901a\u5b66\u79d1',
  'Languages': '\u8bed\u8a00\u5b66\u79d1',
  'Sciences': '\u79d1\u5b66\u5b66\u79d1',
  'Mathematics and Statistics': '\u6570\u5b66\u4e0e\u7edf\u8ba1\u5b66\u79d1',
  'Social Sciences': '\u793e\u4f1a\u79d1\u5b66\u5b66\u79d1',
  'Te Reo M\u0101ori': '\u6bdb\u5229\u8bed\u5b66\u79d1',
  'Technology': '\u6280\u672f\u5b66\u79d1',
  'The Arts': '\u827a\u672f\u5b66\u79d1',
};

// ── Render Metro Honours Panel ──

export function renderMetroNcea(data) {
  const s = data.ncea_summary;
  if (!s) return '';
  const en = _lang === 'en';

  const hasHonours = s.scholarships != null || s.outstanding_merit != null || s.distinction != null;
  const hasRankings = data.subject_rankings && data.subject_rankings.length > 0;
  if (!hasHonours && !hasRankings) return '';

  const title = en ? 'Academic Honours (2023 Graduates)' : '\u5b66\u672f\u8363\u8a89\u4e0e\u6bd5\u4e1a\u6210\u7ee9 (2023\u5c4a\u6bd5\u4e1a\u751f)';

  const infoIcon = (text) => `<span style="cursor:help;display:inline-flex;align-items:center;justify-content:center;width:14px;height:14px;border-radius:50%;background:var(--text-muted);color:var(--bg);font-size:9px;font-weight:700;margin-left:5px;vertical-align:middle;opacity:0.5" title="${text}">i</span>`;

  let honoursHtml = '';
  if (hasHonours) {
    const items = [];
    if (s.scholarships != null) {
      const tipText = en
        ? 'NZQA Scholarship is a separate exam beyond NCEA, taken only by top students. This percentage shows how many graduates passed.'
        : 'NZQA Scholarship \u662f\u5728 NCEA \u4e4b\u4e0a\u7684\u989d\u5916\u5b66\u672f\u8003\u8bd5\uff0c\u53ea\u6709\u9876\u5c16\u5b66\u751f\u53c2\u52a0\u3002';
      items.push(`<div style="flex:1;min-width:150px">
        <div style="font-size:22px;font-weight:700">${s.scholarships}%</div>
        <div style="font-size:12px;font-weight:600">${en ? 'Scholarship Exam Pass Rate' : '\u9ad8\u96be\u5ea6\u5956\u5b66\u91d1\u8003\u8bd5\u901a\u8fc7\u7387'}${infoIcon(tipText)}</div>
        <div style="font-size:10px;color:var(--text-muted);margin-top:2px;line-height:1.3">${en ? "Passed NZ's most challenging academic exam" : '\u901a\u8fc7\u65b0\u897f\u5170\u6700\u9ad8\u96be\u5ea6\u5b66\u672f\u8003\u8bd5\u7684\u6bd5\u4e1a\u751f\u5360\u6bd4'}</div>
      </div>`);
    }
    if (s.distinction != null) {
      const tipText = en
        ? 'NCEA Level 3 endorsed with Excellence means 50+ credits scored Excellence. Students counted here are NOT also counted in Merit.'
        : 'NCEA L3 \u5353\u8d8a\u8ba4\u8bc1\u8981\u6c42 50+ \u5b66\u5206\u8fbe\u5230 Excellence\u3002\u4e0e\u4f18\u826f\u7387\u4e0d\u91cd\u53e0\u3002';
      items.push(`<div style="flex:1;min-width:150px">
        <div style="font-size:22px;font-weight:700">${s.distinction}%</div>
        <div style="font-size:12px;font-weight:600">${en ? 'Excellence Rate' : '\u6bd5\u4e1a\u6210\u7ee9\u4f18\u7b49\u7387'}${infoIcon(tipText)}</div>
        <div style="font-size:10px;color:var(--text-muted);margin-top:2px;line-height:1.3">${en ? 'Most subjects scored Excellence' : '\u591a\u6570\u79d1\u76ee\u8fbe\u5230\u4f18\u7b49\u7684\u6bd5\u4e1a\u751f\u6bd4\u4f8b'}</div>
      </div>`);
    }
    if (s.outstanding_merit != null) {
      const tipText = en
        ? 'NCEA Level 3 endorsed with Merit means 50+ credits scored Merit or above. Students with Excellence are counted separately.'
        : 'NCEA L3 \u4f18\u79c0\u8ba4\u8bc1\u8981\u6c42 50+ \u5b66\u5206\u8fbe\u5230 Merit \u4ee5\u4e0a\u3002\u83b7\u5353\u8d8a\u8ba4\u8bc1\u7684\u5b66\u751f\u53e6\u7b97\u3002';
      items.push(`<div style="flex:1;min-width:150px">
        <div style="font-size:22px;font-weight:700">${s.outstanding_merit}%</div>
        <div style="font-size:12px;font-weight:600">${en ? 'Merit Rate' : '\u6bd5\u4e1a\u6210\u7ee9\u826f\u597d\u7387'}${infoIcon(tipText)}</div>
        <div style="font-size:10px;color:var(--text-muted);margin-top:2px;line-height:1.3">${en ? 'Most subjects scored Merit or above' : '\u591a\u6570\u79d1\u76ee\u8fbe\u5230\u826f\u597d\u7684\u6bd5\u4e1a\u751f\u6bd4\u4f8b'}</div>
      </div>`);
    }
    honoursHtml = `<div style="display:flex;gap:20px;flex-wrap:wrap;margin-top:10px">${items.join('')}</div>`;
  }

  let rankHtml = '';
  if (hasRankings) {
    const intro = en
      ? 'Among all Auckland high schools in NCEA Level 3 pass rate rankings:'
      : '\u5404\u5b66\u79d1\u5728\u5168\u5965\u514b\u5170\u9ad8\u4e2d NCEA L3 \u901a\u8fc7\u7387\u6392\u540d\u4e2d:';
    const parts = data.subject_rankings.map(r => {
      const name = en ? r.subject : (SUBJECT_CN[r.subject] || r.subject + '\u5b66\u79d1');
      const rank = en ? `#${r.rank}` : `\u7b2c${r.rank}\u540d`;
      return `<b>${name}</b> ${rank}`;
    });
    rankHtml = `<div style="margin-top:14px">
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px">${intro}</div>
      <div style="font-size:13px;line-height:1.8">${parts.join(en ? ', ' : '\uff0c')}</div>
    </div>`;
  }

  return `<div style="margin-top:16px;padding-top:14px;border-top:1px solid var(--border)">
    <div style="font-size:13px;font-weight:600;margin-bottom:4px">${title}</div>
    ${honoursHtml}${rankHtml}
    <div style="font-size:10px;color:var(--text-muted);margin-top:10px;text-align:right">${en ? 'Source: Metro Magazine Schools 2025' : '\u6765\u6e90: Metro Magazine Schools 2025'}</div>
  </div>`;
}
