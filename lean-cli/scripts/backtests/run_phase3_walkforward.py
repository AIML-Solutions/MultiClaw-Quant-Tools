#!/usr/bin/env python3
from __future__ import annotations

import glob
import json
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path('/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli')
STAMP = datetime.now(timezone.utc).strftime('%Y-%m-%d_phase3_walkforward')
DOCS = ROOT / 'docs'
OUT_MD = DOCS / f'PHASE3_WALKFORWARD_{STAMP}.md'
OUT_JSON = DOCS / f'PHASE3_WALKFORWARD_{STAMP}.json'

WINDOWS: List[Tuple[str, str]] = [
    ('2014', '2016'),
    ('2017', '2018'),
    ('2019', '2020'),
]


@dataclass
class Sweep:
    project: str
    label: str
    base_params: Dict[str, str]


def sweeps() -> List[Sweep]:
    risk_tickers = 'SPY,QQQ,IWM,EEM,AAPL,BAC,IBM,GOOG'
    def_tickers = 'USO,BNO'
    avwap_tickers = 'SPY,QQQ,IWM,EEM,AAPL,BAC,IBM,USO,BNO'
    return [
        Sweep('baseline-strategy', 'baseline', {'risk_per_trade': '0.004', 'max_positions': '6'}),
        Sweep('regime-ensemble-alpha', 'regime', {
            'include_crypto': 'false',
            'risk_tickers': risk_tickers,
            'def_tickers': def_tickers,
        }),
        Sweep('anchored-vwap-sleeve', 'avwap', {
            'include_crypto': 'false',
            'equity_tickers': avwap_tickers,
        }),
        Sweep('statarb-spread-engine', 'statarb', {}),
        Sweep('options-greeks-vix', 'options', {
            'enable_options': 'true',
            'option_underlying_ticker': 'AAPL',
            'underlying_ticker': 'SPY',
        }),
        Sweep('options-greeks-vix', 'options_fallback', {
            'enable_options': 'false',
            'fallback_equity_mode': 'true',
            'option_underlying_ticker': 'AAPL',
            'underlying_ticker': 'SPY',
        }),
    ]


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


def run_once(sw: Sweep, start: str, end: str) -> Dict:
    name = f"{sw.label}_{start}_{end}"
    out_dir = ROOT / sw.project / 'backtests' / STAMP / name
    if out_dir.exists():
        subprocess.run(['rm', '-rf', str(out_dir)], check=True)
    out_dir.parent.mkdir(parents=True, exist_ok=True)

    params = dict(sw.base_params)
    params['start_year'] = start
    params['end_year'] = end

    cmd = ['lean', 'backtest', sw.project, '--output', str(out_dir), '--backtest-name', name, '--no-update']
    for k, v in params.items():
        cmd += ['--parameter', k, str(v)]

    t0 = datetime.now(timezone.utc)
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    t1 = datetime.now(timezone.utc)

    stats = {}
    summary = glob.glob(str(out_dir / '*-summary.json'))
    if summary:
        with open(summary[0], 'r', encoding='utf-8') as f:
            j = json.load(f)
        stats = j.get('statistics', {})

    return {
        'project': sw.project,
        'sleeve': sw.label,
        'window': f'{start}-{end}',
        'params': params,
        'status_code': p.returncode,
        'duration_sec': round((t1 - t0).total_seconds(), 2),
        'output_dir': str(out_dir),
        'stats': {
            'Total Orders': stats.get('Total Orders'),
            'Net Profit': stats.get('Net Profit'),
            'Sharpe Ratio': stats.get('Sharpe Ratio'),
            'Drawdown': stats.get('Drawdown'),
            'End Equity': stats.get('End Equity'),
            'Total Fees': stats.get('Total Fees'),
            'Portfolio Turnover': stats.get('Portfolio Turnover'),
        },
    }


def main():
    rows: List[Dict] = []

    for sw in sweeps():
        for start, end in WINDOWS:
            print(f"[RUN] {sw.label} {start}-{end}", flush=True)
            r = run_once(sw, start, end)
            rows.append(r)
            print(
                f"[DONE] {sw.label} {start}-{end} code={r['status_code']} "
                f"net={r['stats'].get('Net Profit')} orders={r['stats'].get('Total Orders')}",
                flush=True,
            )

    DOCS.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(rows, indent=2), encoding='utf-8')

    by_sleeve = defaultdict(list)
    for r in rows:
        by_sleeve[r['sleeve']].append(r)

    md = []
    md.append(f'# Phase 3 Walk-Forward Stability — {STAMP}')
    md.append('')
    md.append(f'Generated: {datetime.now(timezone.utc).isoformat()}')
    md.append('')
    md.append(f'JSON: `{OUT_JSON}`')
    md.append('')
    md.append('| Sleeve | Window | Orders | Net Profit | Sharpe | Drawdown | End Equity | Output |')
    md.append('|---|---|---:|---:|---:|---:|---:|---|')

    for r in rows:
        s = r['stats']
        md.append(
            f"| {r['sleeve']} | {r['window']} | {s.get('Total Orders')} | {s.get('Net Profit')} | {s.get('Sharpe Ratio')} | {s.get('Drawdown')} | {s.get('End Equity')} | `{r['output_dir']}` |"
        )

    md.append('')
    md.append('## Stability Summary')
    md.append('')
    md.append('| Sleeve | Windows Positive Net | Avg Net % | Avg Sharpe | Worst Drawdown % |')
    md.append('|---|---:|---:|---:|---:|')

    for sleeve, items in by_sleeve.items():
        nets = [pct(x['stats'].get('Net Profit')) for x in items]
        sharps = [flt(x['stats'].get('Sharpe Ratio')) for x in items]
        dds = [pct(x['stats'].get('Drawdown')) for x in items]

        nets_clean = [x for x in nets if x is not None]
        sharps_clean = [x for x in sharps if x is not None]
        dds_clean = [x for x in dds if x is not None]

        positive = sum(1 for x in nets_clean if x > 0)
        avg_net = (sum(nets_clean) / len(nets_clean)) if nets_clean else None
        avg_sharpe = (sum(sharps_clean) / len(sharps_clean)) if sharps_clean else None
        worst_dd = max(dds_clean) if dds_clean else None

        md.append(
            f"| {sleeve} | {positive}/{len(items)} | "
            f"{('%.3f' % avg_net) if avg_net is not None else 'n/a'} | "
            f"{('%.3f' % avg_sharpe) if avg_sharpe is not None else 'n/a'} | "
            f"{('%.3f' % worst_dd) if worst_dd is not None else 'n/a'} |"
        )

    OUT_MD.write_text('\n'.join(md), encoding='utf-8')
    print(f'REPORT_MD={OUT_MD}')
    print(f'REPORT_JSON={OUT_JSON}')


if __name__ == '__main__':
    main()
