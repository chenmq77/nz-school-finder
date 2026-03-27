/**
 * Table module — column definitions, cell value extraction, formatting, sorting.
 * Extracted from index.html. Pure data + logic, no DOM rendering.
 *
 * Functions that need i18n (t, td, bilingual, esc) access them from the global
 * scope since they're defined before this module loads.
 */

// ── Column Schema ──────────────────────────────────

export const TABLE_COLUMNS = [
  { key:'name',         tKey:'col_name',         fixed:true,  default:true,  gKey:'col_group_basic',      sortable:true,  sortType:'text',   align:'left' },
  { key:'suburb',       tKey:'col_suburb',        fixed:false, default:true,  gKey:'col_group_basic',      sortable:true,  sortType:'text',   align:'left' },
  { key:'school_level', tKey:'col_school_level',  fixed:false, default:true,  gKey:'col_group_basic',      sortable:false, align:'left', autoHide:'year_level' },
  { key:'gender',       tKey:'col_gender',        fixed:false, default:true,  gKey:'col_group_basic',      sortable:false, align:'left', autoHide:'gender' },
  { key:'eqi',          tKey:'col_eqi',           fixed:false, default:true,  gKey:'col_group_basic',      sortable:true,  sortType:'number', align:'right', firstDir:'asc', tipKey:'col_eqi_tip' },
  { key:'roll',         tKey:'col_roll',          fixed:false, default:true,  gKey:'col_group_basic',      sortable:true,  sortType:'number', align:'right', firstDir:'desc' },
  { key:'zone',         tKey:'col_zone',          fixed:false, default:false, gKey:'col_group_basic',      sortable:false, align:'center' },
  { key:'ethnicity',    tKey:'col_ethnicity',     fixed:false, default:false, gKey:'col_group_ethnicity',  sortable:true,  sortType:'number', align:'right', firstDir:'desc' },
  { key:'eth_european', tKey:'col_eth_european',  fixed:false, default:false, gKey:'col_group_ethnicity',  sortable:true,  sortType:'number', align:'right', firstDir:'desc' },
  { key:'eth_maori',    tKey:'col_eth_maori',     fixed:false, default:false, gKey:'col_group_ethnicity',  sortable:true,  sortType:'number', align:'right', firstDir:'desc' },
  { key:'eth_pacific',  tKey:'col_eth_pacific',   fixed:false, default:false, gKey:'col_group_ethnicity',  sortable:true,  sortType:'number', align:'right', firstDir:'desc' },
  { key:'eth_asian',    tKey:'col_eth_asian',     fixed:false, default:false, gKey:'col_group_ethnicity',  sortable:true,  sortType:'number', align:'right', firstDir:'desc' },
  { key:'eth_melaa',    tKey:'col_eth_melaa',     fixed:false, default:false, gKey:'col_group_ethnicity',  sortable:true,  sortType:'number', align:'right', firstDir:'desc' },
  { key:'eth_other',    tKey:'col_eth_other',     fixed:false, default:false, gKey:'col_group_ethnicity',  sortable:true,  sortType:'number', align:'right', firstDir:'desc' },
  // International students group
  { key:'intl',         tKey:'col_intl',          fixed:false, default:false, gKey:'col_group_intl',       sortable:true,  sortType:'number', align:'right', firstDir:'desc' },
  { key:'intl_fee',     tKey:'col_intl_fee',      fixed:false, default:false, gKey:'col_group_intl',       sortable:true,  sortType:'number', align:'right', firstDir:'asc' },
  { key:'intl_homestay',tKey:'col_intl_homestay', fixed:false, default:false, gKey:'col_group_intl',       sortable:true,  sortType:'number', align:'right', firstDir:'asc' },
  { key:'intl_total',   tKey:'col_intl_total',    fixed:false, default:false, gKey:'col_group_intl',       sortable:true,  sortType:'number', align:'right', firstDir:'asc' },
  { key:'ncea_l3',      tKey:'col_ncea_l3',       fixed:false, default:false, gKey:'col_group_intl',       sortable:true,  sortType:'number', align:'right', firstDir:'desc' },
  { key:'ue',           tKey:'col_ue',            fixed:false, default:false, gKey:'col_group_intl',       sortable:true,  sortType:'number', align:'right', firstDir:'desc' },
  // Activities group
  { key:'curriculum',   tKey:'col_curriculum',    fixed:false, default:false, gKey:'col_group_activities', sortable:false, align:'left' },
  { key:'subjects',     tKey:'col_subjects',      fixed:false, default:false, gKey:'col_group_activities', sortable:true,  sortType:'number', align:'right', firstDir:'desc' },
  { key:'sports',       tKey:'col_sports',        fixed:false, default:false, gKey:'col_group_activities', sortable:true,  sortType:'number', align:'right', firstDir:'desc' },
  { key:'arts',         tKey:'col_arts',          fixed:false, default:false, gKey:'col_group_activities', sortable:true,  sortType:'number', align:'right', firstDir:'desc' },
  { key:'clubs',        tKey:'col_clubs',         fixed:false, default:false, gKey:'col_group_activities', sortable:true,  sortType:'number', align:'right', firstDir:'desc' },
];

export const DEFAULT_COLS = TABLE_COLUMNS.filter(c => c.fixed || c.default).map(c => c.key);

export const COL_PRESETS = {
  compact:  ['name', 'suburb', 'school_level', 'gender', 'eqi', 'roll'],
  intl:     ['name', 'eqi', 'roll', 'intl', 'eth_asian', 'intl_fee', 'intl_total', 'ncea_l3', 'ue'],
  local:    ['name', 'suburb', 'school_level', 'gender', 'eqi', 'roll', 'zone', 'ethnicity'],
  full:     ['name', 'suburb', 'eqi', 'roll', 'ue', 'intl_fee', 'curriculum', 'subjects', 'sports', 'arts', 'ethnicity'],
};

// ── Column State ───────────────────────────────────

let _visibleCols = [];
let _tableSort = { key: null, dir: null };

export function getVisibleCols() { return _visibleCols; }
export function setVisibleCols(cols) { _visibleCols = cols; }
export function getTableSort() { return _tableSort; }
export function setTableSort(sort) { _tableSort = sort; }

export function loadVisibleCols() {
  try {
    const saved = localStorage.getItem('schoolColumns');
    if (saved) {
      const parsed = JSON.parse(saved);
      const validKeys = new Set(TABLE_COLUMNS.map(c => c.key));
      const filtered = parsed.filter(k => validKeys.has(k));
      TABLE_COLUMNS.filter(c => c.fixed).forEach(c => {
        if (!filtered.includes(c.key)) filtered.unshift(c.key);
      });
      _visibleCols = filtered.length > 0 ? filtered : [...DEFAULT_COLS];
      return;
    }
  } catch(e) {}
  _visibleCols = [...DEFAULT_COLS];
}

export function saveVisibleCols() {
  try { localStorage.setItem('schoolColumns', JSON.stringify(_visibleCols)); } catch(e) {}
}

export function resetVisibleCols() {
  _visibleCols = [...DEFAULT_COLS];
  _tableSort = { key: null, dir: null };
  saveVisibleCols();
}

// ── Cell Value Extraction ──────────────────────────

export function getCellValue(s, key) {
  const roll = parseInt(s.total_school_roll) || 0;
  switch(key) {
    case 'name': return null;
    case 'suburb': return s.suburb || s.town_city || '';
    case 'tags': return null;
    case 'school_level': return s.school_type ? td('school_type_label', s.school_type) : null;
    case 'gender': return s.gender_of_students ? td('gender', s.gender_of_students) : null;
    case 'eqi': {
      const v = parseFloat(s.equity_index_eqi);
      return isNaN(v) ? null : v;
    }
    case 'roll': return roll || null;
    case 'zone': return s.enrolment_scheme === 'Yes' ? t('col_zone_yes') : '\u2014';
    case 'ethnicity': {
      const eths = [
        { name: '\u6b27\u88d4', val: parseInt(s.european_pakeha) || 0 },
        { name: '\u6bdb\u5229\u88d4', val: parseInt(s.maori) || 0 },
        { name: '\u592a\u5e73\u6d0b\u88d4', val: parseInt(s.pacific) || 0 },
        { name: '\u4e9a\u88d4', val: parseInt(s.asian) || 0 },
        { name: 'MELAA', val: parseInt(s.melaa) || 0 },
        { name: '\u5176\u4ed6', val: parseInt(s.other) || 0 },
      ];
      const max = eths.reduce((a, b) => a.val > b.val ? a : b);
      const pct = roll > 0 ? Math.round(max.val / roll * 100) : 0;
      return pct > 0 ? pct : null;
    }
    case 'eth_european': return roll > 0 ? Math.round((parseInt(s.european_pakeha) || 0) / roll * 100) : null;
    case 'eth_maori': return roll > 0 ? Math.round((parseInt(s.maori) || 0) / roll * 100) : null;
    case 'eth_pacific': return roll > 0 ? Math.round((parseInt(s.pacific) || 0) / roll * 100) : null;
    case 'eth_asian': return roll > 0 ? Math.round((parseInt(s.asian) || 0) / roll * 100) : null;
    case 'eth_melaa': return roll > 0 ? Math.round((parseInt(s.melaa) || 0) / roll * 100) : null;
    case 'eth_other': return roll > 0 ? Math.round((parseInt(s.other) || 0) / roll * 100) : null;
    case 'eth_intl': return roll > 0 ? Math.round((parseInt(s.international) || 0) / roll * 100) : null;
    case 'curriculum': {
      if (!s.curriculum_systems) return null;
      try {
        const systems = JSON.parse(s.curriculum_systems);
        return systems.map(c => c.system || c).join(', ');
      } catch(e) { return s.curriculum_systems; }
    }
    case 'intl': return parseInt(s.international) || null;
    case 'intl_count': return parseInt(s.international) || null;
    case 'intl_fee': return s.intl_tuition_annual || null;
    case 'intl_homestay': return s.intl_homestay_weekly || null;
    case 'intl_total': {
      const tuition = parseFloat(s.intl_tuition_annual);
      const homestay = parseFloat(s.intl_homestay_weekly);
      if (!tuition) return null;
      return homestay ? Math.round(tuition + homestay * 40) : null;
    }
    case 'ncea_l3': return s.ncea_l3 != null ? parseFloat(s.ncea_l3) : null;
    case 'ue': return s.ue_percentage != null ? parseFloat(s.ue_percentage) : null;
    case 'fee': return s.intl_tuition_annual || null;
    case 'subjects': return s.subjects_count || null;
    case 'sports': return s.sports_count || null;
    case 'arts': return s.music_count || null;
    case 'clubs': return s.activities_count || null;
    default: return null;
  }
}

// ── Cell Formatting ────────────────────────────────

export function formatCell(key, val, s) {
  if (key === 'name') {
    const cn = s.school_name_cn;
    const en = s.school_name || '';
    if (_lang === 'en') {
      return `<div class="td-name"><div class="cn">${esc(en)}</div></div>`;
    }
    if (cn) return `<div class="td-name"><div class="cn">${esc(cn)}</div><div class="en">${esc(en)}</div></div>`;
    return `<div class="td-name"><div class="cn">${esc(en)}</div></div>`;
  }
  if (key === 'tags') {
    let tags = [];
    if (s.school_type) tags.push(`<span class="sc-badge">${esc(td('school_type_label', s.school_type))}</span>`);
    if (s.gender_of_students && s.gender_of_students !== 'Co-Educational')
      tags.push(`<span class="sc-badge">${esc(td('gender', s.gender_of_students))}</span>`);
    if (s.authority && s.authority !== 'State')
      tags.push(`<span class="sc-badge">${esc(td('authority', s.authority))}</span>`);
    return tags.join(' ');
  }
  if (key === 'school_level') {
    if (!s.school_type) return '<span class="td-null">--</span>';
    const cat = TRANSLATIONS.data['school_type_label'];
    const item = cat && cat[s.school_type];
    return item ? bilingual(item.en, item.cn) : esc(s.school_type);
  }
  if (key === 'gender') {
    if (!s.gender_of_students) return '<span class="td-null">--</span>';
    const cat = TRANSLATIONS.data['gender'];
    const item = cat && cat[s.gender_of_students];
    return item ? bilingual(item.en, item.cn) : esc(s.gender_of_students);
  }
  if (val === null || val === undefined) return '<span class="td-null">\u2014</span>';
  if (key === 'eqi') {
    const v = parseFloat(val);
    const color = v <= 429 ? '#2a6560' : v <= 493 ? '#7a5c3a' : '#8a3038';
    return `<span style="color:${color};font-weight:600">${Math.round(v)}</span>`;
  }
  if (key === 'intl') {
    const count = parseInt(s.international) || 0;
    const roll = parseInt(s.total_school_roll) || 0;
    if (!count) return '<span class="td-null">\u2014</span>';
    const pct = roll > 0 ? Math.round(count / roll * 100) : 0;
    return `${count.toLocaleString()} (${pct}%)`;
  }
  if (key === 'roll' || key === 'intl_count') return parseInt(val).toLocaleString();
  if (key === 'fee' || key === 'intl_fee' || key === 'intl_total') return '$' + parseFloat(val).toLocaleString();
  if (key === 'intl_homestay') return '$' + parseFloat(val).toLocaleString() + '/w';
  if (key === 'ncea_l3') return parseFloat(val).toFixed(1) + '%';
  if (key === 'ue') return Math.round(parseFloat(val)) + '%';
  if (key === 'ethnicity') {
    const roll = parseInt(s.total_school_roll) || 0;
    const eths = [
      { name: '\u6b27\u88d4', val: parseInt(s.european_pakeha) || 0 },
      { name: '\u6bdb\u5229\u88d4', val: parseInt(s.maori) || 0 },
      { name: '\u592a\u5e73\u6d0b\u88d4', val: parseInt(s.pacific) || 0 },
      { name: '\u4e9a\u88d4', val: parseInt(s.asian) || 0 },
      { name: 'MELAA', val: parseInt(s.melaa) || 0 },
      { name: '\u5176\u4ed6', val: parseInt(s.other) || 0 },
    ];
    const max = eths.reduce((a, b) => a.val > b.val ? a : b);
    const pct = roll > 0 ? Math.round(max.val / roll * 100) : 0;
    return pct > 0 ? `${max.name} ${pct}%` : '<span class="td-null">\u2014</span>';
  }
  if (key.startsWith('eth_')) return val + '%';
  if (key === 'curriculum') return esc(String(val));
  return esc(String(val));
}

// ── Sorting ────────────────────────────────────────

export function sortTableData(results) {
  if (!_tableSort.key) return results;
  const col = TABLE_COLUMNS.find(c => c.key === _tableSort.key);
  if (!col || !col.sortable) return results;

  const sorted = [...results];
  sorted.sort((a, b) => {
    let va = getCellValue(a, _tableSort.key);
    let vb = getCellValue(b, _tableSort.key);
    if (va === null && vb === null) return 0;
    if (va === null) return 1;
    if (vb === null) return -1;
    if (_tableSort.key === 'name') {
      va = (a.school_name_cn || a.school_name || '').toLowerCase();
      vb = (b.school_name_cn || b.school_name || '').toLowerCase();
    }
    let cmp = 0;
    if (col.sortType === 'number') {
      cmp = parseFloat(va) - parseFloat(vb);
    } else {
      cmp = String(va).localeCompare(String(vb), 'zh');
    }
    return _tableSort.dir === 'desc' ? -cmp : cmp;
  });
  return sorted;
}

/** Cycle sort state: default dir -> reverse -> clear */
export function cycleSort(key) {
  const col = TABLE_COLUMNS.find(c => c.key === key);
  if (!col || !col.sortable) return;

  if (_tableSort.key === key) {
    if (_tableSort.dir === (col.firstDir || 'desc')) {
      _tableSort.dir = _tableSort.dir === 'asc' ? 'desc' : 'asc';
    } else {
      _tableSort = { key: null, dir: null };
    }
  } else {
    _tableSort = { key: key, dir: col.firstDir || 'desc' };
  }
}

/** Find column definition by key */
export function findColumn(key) {
  return TABLE_COLUMNS.find(c => c.key === key);
}

/** Get visible column definitions */
export function getVisibleColumnDefs() {
  return _visibleCols.map(k => TABLE_COLUMNS.find(c => c.key === k)).filter(Boolean);
}
