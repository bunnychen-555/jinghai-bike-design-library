/* Google Sheets content database — VELO / ARCHIVE V3 */
const SHEET_ID = '1UF9OWCELbomfYCVPtxkSUZD4fOVbG6DI4yOdr5mAC1A';
const SHEET_NAME = '资料库';
const SHEET_ENDPOINT = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:json&sheet=${encodeURIComponent(SHEET_NAME)}`;

function cellValue(row, index) {
  const cell = row.c && row.c[index];
  if (!cell) return '';
  return cell.f ?? cell.v ?? '';
}

function recordFromRow(row, index) {
  const status = String(cellValue(row, 12)).trim();
  if (status !== '已通过') return null;

  const rawId = String(cellValue(row, 0)).trim();
  const sequence = rawId.match(/\d+/)?.[0] || String(index + 1);
  const brand = String(cellValue(row, 2)).trim();
  const title = String(cellValue(row, 1)).trim();
  const summary = String(cellValue(row, 8)).trim();

  if (!brand || !title) return null;

  return {
    id: sequence.padStart(2, '0'),
    brand,
    title,
    en: `${String(cellValue(row, 4)).toUpperCase()} / DESIGN REFERENCE`,
    year: String(cellValue(row, 7)).trim(),
    cat: String(cellValue(row, 3)).trim(),
    style: String(cellValue(row, 4)).trim(),
    material: String(cellValue(row, 5)).trim(),
    focus: String(cellValue(row, 6)).trim(),
    image: String(cellValue(row, 9)).trim(),
    intro: summary,
    note: summary,
    sourceUrl: String(cellValue(row, 10)).trim(),
    sourceName: String(cellValue(row, 11)).trim()
  };
}

function setDatabaseStatus(label) {
  const edition = document.querySelector('.edition');
  if (edition) edition.textContent = label;
}

async function loadSheetDatabase() {
  setDatabaseStatus('CONNECTING · DATABASE');

  try {
    const response = await fetch(SHEET_ENDPOINT, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const text = await response.text();
    const start = text.indexOf('{');
    const end = text.lastIndexOf('}');
    if (start < 0 || end < start) throw new Error('Invalid Google Sheets response');

    const payload = JSON.parse(text.slice(start, end + 1));
    const records = (payload.table?.rows || [])
      .map(recordFromRow)
      .filter(Boolean);

    if (!records.length) throw new Error('No approved records');

    bikes.splice(0, bikes.length, ...records);
    const allButton = document.querySelector('.filters button[data-tag="全部"]');
    if (allButton) allButton.textContent = `全部 ${String(records.length).padStart(2, '0')}`;
    setDatabaseStatus(`LIVE DATABASE · ${String(records.length).padStart(2, '0')} RECORDS`);
    render();
  } catch (error) {
    setDatabaseStatus('OFFLINE CACHE · 03 RECORDS');
    console.warn('Google Sheets database unavailable; using local cache.', error);
  }
}

loadSheetDatabase();
