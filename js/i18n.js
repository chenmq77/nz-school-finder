/**
 * Internationalization (i18n) module — extracted from index.html
 * Depends on global TRANSLATIONS object from translations.js
 */
import { esc } from './utils.js';

/** Current language: 'en' | 'cn' | 'both' */
let _lang = 'cn';

export function getLang() { return _lang; }

export function setLang(lang) {
  _lang = lang;
  localStorage.setItem('lang', lang);
}

export function initLang() {
  _lang = localStorage.getItem('lang') || 'cn';
  return _lang;
}

/** Translate a UI key */
export function t(key) {
  const item = TRANSLATIONS.ui[key];
  if (!item) return key;
  if (_lang === 'en') return item.en;
  if (_lang === 'cn') return item.cn || item.en;
  return item.cn ? `${item.en} / ${item.cn}` : item.en;
}

/** Translate a data enum value (school_type, authority, etc.) */
export function td(category, value) {
  if (!value) return '--';
  const cat = TRANSLATIONS.data[category];
  if (!cat) return value;
  const item = cat[value];
  if (!item) return value;
  if (_lang === 'en') return item.en;
  if (_lang === 'cn') return item.cn || item.en;
  return item.cn ? `${item.en} / ${item.cn}` : item.en;
}

/** Render bilingual HTML */
export function bilingual(en, cn) {
  if (!cn) return esc(en || '--');
  if (_lang === 'en') return esc(en);
  if (_lang === 'cn') return esc(cn);
  return `${esc(en)}<div style="font-size:0.85em;color:var(--text-muted);margin-top:2px">${esc(cn)}</div>`;
}

/** Check if current language is English */
export function isEn() { return _lang === 'en'; }
