/**
 * Export module — shared image export infrastructure.
 * Extracted from index.html.
 *
 * Individual export functions (exportNceaCard, exportSchoolCard, etc.)
 * remain in index.html for now due to heavy DOM/state dependencies.
 */
import { showToast } from './utils.js';

/**
 * Render a DOM element as a PNG image and trigger download.
 * @param {HTMLElement} div - element to render (will be temporarily appended to body)
 * @param {string} filename - download filename
 * @param {HTMLElement|null} loadingBtn - optional button to show loading state
 */
export async function exportDivAsImage(div, filename, loadingBtn) {
  if (!window.html2canvas) { showToast(t('col_export_no_lib')); return; }
  if (loadingBtn) { loadingBtn.textContent = t('col_export_loading'); loadingBtn.disabled = true; }

  document.body.appendChild(div);
  try {
    const canvas = await html2canvas(div, { scale: 2, useCORS: true, backgroundColor: '#F8F6F2' });
    await new Promise((resolve) => {
      canvas.toBlob(blob => {
        if (!blob) { showToast(t('col_export_fail')); resolve(); return; }
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        if (/iPad|iPhone|iPod/.test(navigator.userAgent)) { window.open(url); }
        else { a.click(); }
        setTimeout(() => URL.revokeObjectURL(url), 5000);
        resolve();
      }, 'image/png');
    });
  } catch (e) {
    showToast(t('col_export_fail'));
  } finally {
    if (div.parentNode) div.parentNode.removeChild(div);
    if (loadingBtn) { loadingBtn.textContent = t('col_export'); loadingBtn.disabled = false; }
  }
}

/**
 * Build a standard footer for exported cards.
 * @returns {HTMLElement}
 */
export function buildExportFooter() {
  const footer = document.createElement('div');
  footer.style.cssText = 'margin-top:auto;padding-top:12px;border-top:1px solid #eee;font-size:10px;color:#bbb;display:flex;justify-content:space-between;';
  footer.innerHTML = `<span>nzschoolfinder.com</span><span>${new Date().toLocaleDateString('en-CA', {timeZone: 'Pacific/Auckland'})}</span>`;
  return footer;
}

/**
 * Generate a timestamped filename for exports.
 * @param {string} prefix - e.g. 'ncea-card'
 * @param {string} ext - e.g. 'png'
 * @returns {string}
 */
export function exportFilename(prefix, ext = 'png') {
  return `${prefix}-${new Date().toISOString().split('T')[0]}.${ext}`;
}
