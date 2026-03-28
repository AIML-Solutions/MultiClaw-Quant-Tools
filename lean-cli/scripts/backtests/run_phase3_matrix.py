#!/usr/bin/env python3
from __future__ import annotations

import glob
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path('/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli')
STAMP = datetime.now(timezone.utc).strftime('%Y-%m-%d_phase3_matrix')
REPORT_DIR = ROOT / 'docs'
REPORT_MD = REPORT_DIR / f'PHASE3_BACKTEST_MATRIX_{STAMP}.md'
REPORT_JSON = REPORT_DIR / f'PHASE3_BACKTEST_MATRIX_{STAMP}.json'


@dataclass
class Case:
    project: str
    name: str
    params: Dict[str, str]


def cases() -> List[Case]:
    risk_tickers = 'SPY,QQQ,IWM,EEM,AAPL,BAC,IBM,GOOG'
    def_tickers = 'USO,BNO'
    avwap_tickers = 'SPY,QQQ,IWM,EEM,AAPL,BAC,IBM,USO,BNO'

    return [
        Case('baseline-strategy', 'baseline_phase3_core', {
            'start_year': '2018', 'end_year': '2020', 'risk_per_trade': '0.004', 'max_positions': '6'
        }),
        Case('baseline-strategy', 'baseline_phase3_oos', {
            'start_year': '2019', 'end_year': '2021', 'risk_per_trade': '0.004', 'max_positions': '6'
        }),

        Case('regime-ensemble-alpha', 'regime_phase3_core', {
            'start_year': '2014', 'end_year': '2020', 'include_crypto': 'false',
            'risk_tickers': risk_tickers, 'def_tickers': def_tickers
        }),
        Case('regime-ensemble-alpha', 'regime_phase3_oos', {
            'start_year': '2019', 'end_year': '2021', 'include_crypto': 'false',
            'risk_tickers': risk_tickers, 'def_tickers': def_tickers
        }),

        Case('anchored-vwap-sleeve', 'avwap_phase3_core', {
            'start_year': '2014', 'end_year': '2020', 'include_crypto': 'false', 'equity_tickers': avwap_tickers
        }),
        Case('anchored-vwap-sleeve', 'avwap_phase3_conservative', {
            'start_year': '2014', 'end_year': '2020', 'include_crypto': 'false', 'equity_tickers': avwap_tickers,
            'risk_per_trade': '0.0025', 'max_positions': '2', 'max_position_weight': '0.10',
            'entry_gap_pct_max': '0.03', 'max_entries_per_day': '1'
        }),
        Case('anchored-vwap-sleeve', 'avwap_phase3_oos', {
            'start_year': '2019', 'end_year': '2021', 'include_crypto': 'false', 'equity_tickers': avwap_tickers
        }),

        Case('statarb-spread-engine', 'statarb_phase3_core', {
            'start_year': '2014', 'end_year': '2020'
        }),
        Case('statarb-spread-engine', 'statarb_phase3_tighter', {
            'start_year': '2014', 'end_year': '2020',
            'entry_z': '3.2', 'min_edge_z': '1.8', 'roundtrip_cost_pct': '0.0022', 'pair_risk_pct': '0.02'
        }),
        Case('statarb-spread-engine', 'statarb_phase3_oos', {
            'start_year': '2019', 'end_year': '2021'
        }),

        Case('options-greeks-vix', 'options_phase3_core', {
            'start_year': '2014', 'end_year': '2015', 'enable_options': 'true',
            'option_underlying_ticker': 'AAPL', 'underlying_ticker': 'SPY'
        }),
        Case('options-greeks-vix', 'options_phase3_fallback', {
            'start_year': '2014', 'end_year': '2015', 'enable_options': 'false',
            'fallback_equity_mode': 'true', 'option_underlying_ticker': 'AAPL', 'underlying_ticker': 'SPY'
        }),
    ]


def run_case(c: Case) -> Dict:
    out_dir = ROOT / c.project / 'backtests' / STAMP / c.name
    if out_dir.exists():
        subprocess.run(['rm', '-rf', str(out_dir)], check=True)
    out_dir.parent.mkdir(parents=True, exist_ok=True)

    cmd = ['lean', 'backtest', c.project, '--output', str(out_dir), '--backtest-name', c.name, '--no-update']
    for k, v in c.params.items():
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
        'project': c.project,
        'scenario': c.name,
        'params': c.params,
        'status_code': p.returncode,
        'duration_sec': round((t1 - t0).total_seconds(), 2),
        'output_dir': str(out_dir),
        'stats': {
            'Total Orders': stats.get('Total Orders'),
            'Net Profit': stats.get('Net Profit'),
            'End Equity': stats.get('End Equity'),
            'Drawdown': stats.get('Drawdown'),
            'Sharpe Ratio': stats.get('Sharpe Ratio'),
            'Sortino Ratio': stats.get('Sortino Ratio'),
            'Total Fees': stats.get('Total Fees'),
            'Portfolio Turnover': stats.get('Portfolio Turnover'),
        },
    }


def main():
    rows: List[Dict] = []

    for c in cases():
        print(f"[RUN] {c.project}:{c.name}", flush=True)
        r = run_case(c)
        rows.append(r)
        print(
            f"[DONE] {c.project}:{c.name} code={r['status_code']} "
            f"net={r['stats'].get('Net Profit')} orders={r['stats'].get('Total Orders')}",
            flush=True,
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(rows, indent=2), encoding='utf-8')

    md = []
    md.append(f"# Phase 3 Backtest Matrix — {STAMP}")
    md.append('')
    md.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    md.append('')
    md.append(f"JSON: `{REPORT_JSON}`")
    md.append('')
    md.append('| Project | Scenario | Orders | Net Profit | Sharpe | Drawdown | End Equity | Fees | Turnover | Output |')
    md.append('|---|---|---:|---:|---:|---:|---:|---:|---:|---|')

    for r in rows:
        s = r['stats']
        md.append(
            f"| {r['project']} | {r['scenario']} | {s.get('Total Orders')} | {s.get('Net Profit')} | "
            f"{s.get('Sharpe Ratio')} | {s.get('Drawdown')} | {s.get('End Equity')} | {s.get('Total Fees')} | "
            f"{s.get('Portfolio Turnover')} | `{r['output_dir']}` |"
        )

    REPORT_MD.write_text('\n'.join(md), encoding='utf-8')
    print(f"REPORT_MD={REPORT_MD}")
    print(f"REPORT_JSON={REPORT_JSON}")


if __name__ == '__main__':
    main()
