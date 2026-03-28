#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path('/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli')
DOCS = ROOT / 'docs'
STAMP = datetime.now(timezone.utc).strftime('%Y-%m-%d_phase3_allocator')
OUT_MD = DOCS / f'PHASE3_SLEEVE_ALLOCATOR_{STAMP}.md'
OUT_JSON = DOCS / f'PHASE3_SLEEVE_ALLOCATOR_{STAMP}.json'


def latest_json(prefix: str) -> Optional[Path]:
    cands = sorted(DOCS.glob(f'{prefix}*.json'))
    return cands[-1] if cands else None


def pct(v):
    if v is None:
        return None
    s = str(v).replace('%', '').replace(',', '').strip()
    try:
        return float(s)
    except Exception:
        return None


def flt(v):
    if v is None:
        return None
    s = str(v).replace('$', '').replace(',', '').strip()
    try:
        return float(s)
    except Exception:
        return None


def score_row(row: Dict) -> float:
    st = row.get('stats', {})
    net = pct(st.get('Net Profit'))
    sharpe = flt(st.get('Sharpe Ratio'))
    dd = pct(st.get('Drawdown'))

    if net is None or sharpe is None or dd is None:
        return -999.0

    # Robustness-oriented composite: reward return/sharpe, penalize drawdown.
    return net + 2.5 * sharpe - 0.6 * dd


def normalize(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(0.0, w) for w in weights.values())
    if total <= 0:
        return {k: 0.0 for k in weights}
    return {k: max(0.0, w) / total for k, w in weights.items()}


def main():
    matrix_path = latest_json('PHASE3_BACKTEST_MATRIX_')
    if matrix_path is None:
        raise SystemExit('Phase3 matrix JSON not found. Run run_phase3_matrix.py first.')

    rows = json.loads(matrix_path.read_text())

    # Keep one representative scenario per sleeve family.
    families = {
        'baseline-strategy': [],
        'regime-ensemble-alpha': [],
        'anchored-vwap-sleeve': [],
        'statarb-spread-engine': [],
        'options-greeks-vix': [],
    }

    for r in rows:
        fam = r.get('project')
        if fam in families:
            families[fam].append(r)

    selected = {}
    for fam, fam_rows in families.items():
        if not fam_rows:
            continue
        fam_rows = sorted(fam_rows, key=score_row, reverse=True)
        selected[fam] = fam_rows[0]

    # Build sleeve scores and filter weak sleeves.
    sleeve_scores = {}
    for fam, r in selected.items():
        st = r.get('stats', {})
        net = pct(st.get('Net Profit')) or 0.0
        sharpe = flt(st.get('Sharpe Ratio')) or 0.0
        dd = pct(st.get('Drawdown')) or 99.0

        # Only allocate to sleeves with positive net and acceptable drawdown.
        if net <= 0.0:
            sleeve_scores[fam] = 0.0
            continue
        if dd > 20.0:
            sleeve_scores[fam] = 0.0
            continue

        sleeve_scores[fam] = max(0.0, net * (1.0 + max(-0.5, sharpe))) / max(1.0, dd)

    weights = normalize(sleeve_scores)

    out = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'matrix_source': str(matrix_path),
        'selected': selected,
        'scores': sleeve_scores,
        'weights': weights,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2), encoding='utf-8')

    md = []
    md.append(f'# Phase 3 Sleeve Allocator — {STAMP}')
    md.append('')
    md.append(f'Generated: {out["generated_at"]}')
    md.append('')
    md.append(f'Source matrix: `{matrix_path}`')
    md.append(f'JSON artifact: `{OUT_JSON}`')
    md.append('')
    md.append('| Sleeve | Selected Scenario | Net Profit | Sharpe | Drawdown | Score | Suggested Weight |')
    md.append('|---|---|---:|---:|---:|---:|---:|')

    for fam in families.keys():
        r = selected.get(fam)
        if r is None:
            md.append(f'| {fam} | n/a | n/a | n/a | n/a | 0.0000 | 0.0000 |')
            continue
        st = r.get('stats', {})
        md.append(
            f"| {fam} | {r.get('scenario')} | {st.get('Net Profit')} | {st.get('Sharpe Ratio')} | {st.get('Drawdown')} | "
            f"{sleeve_scores.get(fam,0.0):.4f} | {weights.get(fam,0.0):.4f} |"
        )

    md.append('')
    md.append('## Allocation Rule')
    md.append('- Zero weight if net profit <= 0 or drawdown > 20%.')
    md.append('- Otherwise score = (net% * (1 + sharpe_clamped)) / drawdown%.')
    md.append('- Normalize positive scores to 100% total.')

    OUT_MD.write_text('\n'.join(md), encoding='utf-8')
    print(f'REPORT_MD={OUT_MD}')
    print(f'REPORT_JSON={OUT_JSON}')


if __name__ == '__main__':
    main()
