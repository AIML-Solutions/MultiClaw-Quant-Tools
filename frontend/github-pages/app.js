async function fetchJson(path) {
  const r = await fetch(path, { cache: 'no-store' });
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
}

function cell(tr, text) {
  const td = document.createElement('td');
  td.textContent = text ?? '';
  tr.appendChild(td);
}

function addRow(tbody, values) {
  const tr = document.createElement('tr');
  values.forEach(v => cell(tr, v));
  tbody.appendChild(tr);
}

async function loadStrategyMatrix() {
  const data = await fetchJson('data/PHASE3_BACKTEST_MATRIX.json');
  const tbody = document.querySelector('#strategy-table tbody');
  tbody.innerHTML = '';
  for (const row of data) {
    const s = row.stats || {};
    addRow(tbody, [
      row.project,
      row.scenario,
      s['Net Profit'],
      s['Sharpe Ratio'],
      s['Drawdown'],
      s['Total Orders']
    ]);
  }
}

async function loadWalkforward() {
  const data = await fetchJson('data/PHASE3_WALKFORWARD.json');
  const tbody = document.querySelector('#walk-table tbody');
  tbody.innerHTML = '';
  for (const row of data) {
    const s = row.stats || {};
    addRow(tbody, [
      row.sleeve,
      row.window,
      s['Net Profit'],
      s['Sharpe Ratio'],
      s['Drawdown'],
      s['Total Orders']
    ]);
  }
}

async function loadAllocator() {
  const data = await fetchJson('data/PHASE3_ALLOCATOR.json');
  const tbody = document.querySelector('#alloc-table tbody');
  tbody.innerHTML = '';

  const selected = data.selected || {};
  const scores = data.scores || {};
  const weights = data.weights || {};

  for (const sleeve of Object.keys(weights)) {
    addRow(tbody, [
      sleeve,
      (selected[sleeve] || {}).scenario || 'n/a',
      weights[sleeve]?.toFixed?.(4) ?? weights[sleeve],
      scores[sleeve]?.toFixed?.(4) ?? scores[sleeve]
    ]);
  }
}

async function loadPaperSnapshot() {
  try {
    const data = await fetchJson('data/PAPER_SNAPSHOT.json');
    document.getElementById('paper-json').textContent = JSON.stringify(data, null, 2);
  } catch (_) {
    document.getElementById('paper-json').textContent = 'No paper snapshot found in data/PAPER_SNAPSHOT.json';
  }
}

function renderArtifacts() {
  const div = document.getElementById('artifact-list');
  div.innerHTML = `
    <ul>
      <li><a href="data/PHASE3_BACKTEST_MATRIX.md" target="_blank">Phase 3 Matrix (md)</a></li>
      <li><a href="data/PHASE3_WALKFORWARD.md" target="_blank">Phase 3 Walk-Forward (md)</a></li>
      <li><a href="data/PHASE3_ALLOCATOR.md" target="_blank">Phase 3 Allocator (md)</a></li>
      <li><a href="data/PHASE3_METHOD_VALIDITY.md" target="_blank">Method Validity Report</a></li>
      <li><a href="data/PHASE3_DATA_QUALITY_AUDIT.md" target="_blank">Data Quality Audit</a></li>
      <li><a href="data/RUN_LEDGER.md" target="_blank">Run Ledger</a></li>
      <li><a href="data/ARXIV_DIGEST.md" target="_blank">ArXiv Digest</a></li>
    </ul>
  `;
}

async function main() {
  renderArtifacts();
  const errors = [];

  for (const fn of [loadStrategyMatrix, loadWalkforward, loadAllocator, loadPaperSnapshot]) {
    try {
      await fn();
    } catch (e) {
      errors.push(String(e));
    }
  }

  if (errors.length) {
    console.warn('Dashboard load warnings:', errors);
  }
}

main();
