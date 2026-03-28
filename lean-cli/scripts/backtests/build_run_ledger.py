#!/usr/bin/env python3
"""
Build a run ledger of matrix/walkforward/tuning outputs for auditability.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path('/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli/docs')
OUT_JSON = DOCS / 'RUN_LEDGER.json'
OUT_MD = DOCS / 'RUN_LEDGER.md'

PATTERNS = {
    'phase2_matrix': r'^PHASE2_BACKTEST_MATRIX_.*\.json$',
    'phase2_oos': r'^PHASE2_OOS_VALIDATION_.*\.json$',
    'phase2_tuning': r'^PHASE2_TUNING_.*\.json$',
    'phase3_matrix': r'^PHASE3_BACKTEST_MATRIX_.*\.json$',
    'phase3_walkforward': r'^PHASE3_WALKFORWARD_.*\.json$',
    'phase3_allocator': r'^PHASE3_SLEEVE_ALLOCATOR_.*\.json$',
}


def latest(pattern: str):
    rx = re.compile(pattern)
    cands = sorted([p for p in DOCS.iterdir() if p.is_file() and rx.match(p.name)])
    return cands[-1] if cands else None


def summarize_json(path: Path):
    j = json.loads(path.read_text())
    if isinstance(j, dict):
        if 'weights' in j:
            return {
                'type': 'allocator',
                'rows': len(j.get('weights', {})),
            }
        return {'type': 'dict', 'keys': list(j.keys())[:12]}
    if isinstance(j, list):
        return {'type': 'list', 'rows': len(j)}
    return {'type': type(j).__name__}


def main():
    rows = []
    for lane, pat in PATTERNS.items():
        p = latest(pat)
        if not p:
            continue
        stat = p.stat()
        summary = summarize_json(p)
        rows.append({
            'lane': lane,
            'path': str(p),
            'name': p.name,
            'modified_utc': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            'summary': summary,
        })

    rows = sorted(rows, key=lambda x: x['modified_utc'], reverse=True)

    OUT_JSON.write_text(json.dumps({
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'rows': rows,
    }, indent=2), encoding='utf-8')

    md = ['# Run Ledger', '', f"Generated: {datetime.now(timezone.utc).isoformat()}", '']
    md.append('| Lane | File | Modified UTC | Summary |')
    md.append('|---|---|---|---|')
    for r in rows:
        md.append(f"| {r['lane']} | `{r['name']}` | {r['modified_utc']} | `{r['summary']}` |")

    OUT_MD.write_text('\n'.join(md), encoding='utf-8')
    print(OUT_JSON)
    print(OUT_MD)


if __name__ == '__main__':
    main()
