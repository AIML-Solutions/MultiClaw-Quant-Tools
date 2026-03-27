#!/usr/bin/env python3
from __future__ import annotations

import glob
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path('/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli')
STAMP = datetime.now(timezone.utc).strftime('%Y-%m-%d_phase2_tuning')
REPORT_DIR = ROOT / 'docs'
REPORT_MD = REPORT_DIR / f'PHASE2_TUNING_{STAMP}.md'
REPORT_JSON = REPORT_DIR / f'PHASE2_TUNING_{STAMP}.json'


def pct_to_float(v):
    if v is None:
        return None
    s = str(v).strip().replace('%', '')
    try:
        return float(s)
    except Exception:
        return None


def num(v):
    if v is None:
        return None
    s = str(v).strip().replace('$', '').replace(',', '')
    try:
        return float(s)
    except Exception:
        return None


def run_backtest(project: str, scenario: str, params: Dict[str, str], group: str):
    out_dir = ROOT / project / 'backtests' / STAMP / group / scenario
    if out_dir.exists():
        subprocess.run(['rm', '-rf', str(out_dir)], check=True)
    out_dir.parent.mkdir(parents=True, exist_ok=True)

    cmd = ['lean', 'backtest', project, '--output', str(out_dir), '--backtest-name', scenario, '--no-update']
    for k, v in params.items():
        cmd += ['--parameter', k, str(v)]

    t0 = datetime.now(timezone.utc)
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    t1 = datetime.now(timezone.utc)

    stats = {}
    files = glob.glob(str(out_dir / '*-summary.json'))
    if files:
        with open(files[0], 'r', encoding='utf-8') as f:
            j = json.load(f)
        stats = j.get('statistics', {})

    return {
        'project': project,
        'scenario': scenario,
        'group': group,
        'params': params,
        'status_code': p.returncode,
        'duration_sec': round((t1 - t0).total_seconds(), 2),
        'output_dir': str(out_dir),
        'stats': {
            'Net Profit': stats.get('Net Profit'),
            'Sharpe Ratio': stats.get('Sharpe Ratio'),
            'Drawdown': stats.get('Drawdown'),
            'End Equity': stats.get('End Equity'),
            'Total Orders': stats.get('Total Orders'),
            'Total Fees': stats.get('Total Fees'),
        },
    }


def sort_key(row):
    net = pct_to_float(row['stats'].get('Net Profit'))
    sharpe = num(row['stats'].get('Sharpe Ratio'))
    dd = pct_to_float(row['stats'].get('Drawdown'))
    return (
        -999 if net is None else net,
        -999 if sharpe is None else sharpe,
        999 if dd is None else -dd,
    )


def main():
    runs: List[dict] = []

    risk_tickers = 'SPY,QQQ,IWM,EEM,AAPL,BAC,IBM,GOOG'
    def_tickers = 'USO,BNO'
    avwap_tickers = 'SPY,QQQ,IWM,EEM,AAPL,BAC,IBM,USO,BNO'

    regime_is = [
        ('regime_cfg_a', {'start_year':'2014','end_year':'2018','include_crypto':'false','risk_tickers':risk_tickers,'def_tickers':def_tickers,'rebalance_days':'5','target_portfolio_vol':'0.14','max_weight':'0.18','max_turnover_per_rebalance':'0.35'}),
        ('regime_cfg_b', {'start_year':'2014','end_year':'2018','include_crypto':'false','risk_tickers':risk_tickers,'def_tickers':def_tickers,'rebalance_days':'7','target_portfolio_vol':'0.12','max_weight':'0.14','max_turnover_per_rebalance':'0.25'}),
        ('regime_cfg_c', {'start_year':'2014','end_year':'2018','include_crypto':'false','risk_tickers':risk_tickers,'def_tickers':def_tickers,'rebalance_days':'10','target_portfolio_vol':'0.10','max_weight':'0.12','max_turnover_per_rebalance':'0.20','defensive_floor':'0.20'}),
        ('regime_cfg_d', {'start_year':'2014','end_year':'2018','include_crypto':'false','risk_tickers':risk_tickers,'def_tickers':def_tickers,'rebalance_days':'3','target_portfolio_vol':'0.12','max_weight':'0.16','max_turnover_per_rebalance':'0.30'}),
    ]

    avwap_is = [
        ('avwap_cfg_a', {'start_year':'2014','end_year':'2018','include_crypto':'false','equity_tickers':avwap_tickers,'risk_per_trade':'0.004','max_positions':'5','max_position_weight':'0.20','trail_atr_mult':'1.9'}),
        ('avwap_cfg_b', {'start_year':'2014','end_year':'2018','include_crypto':'false','equity_tickers':avwap_tickers,'risk_per_trade':'0.003','max_positions':'4','max_position_weight':'0.15','trail_atr_mult':'1.8'}),
        ('avwap_cfg_c', {'start_year':'2014','end_year':'2018','include_crypto':'false','equity_tickers':avwap_tickers,'risk_per_trade':'0.0025','max_positions':'3','max_position_weight':'0.12','trail_atr_mult':'1.6'}),
        ('avwap_cfg_d', {'start_year':'2014','end_year':'2018','include_crypto':'false','equity_tickers':avwap_tickers,'risk_per_trade':'0.0035','max_positions':'4','max_position_weight':'0.18','trail_atr_mult':'2.2','min_trail_pct':'0.025'}),
    ]

    statarb_is = [
        ('statarb_cfg_a', {'start_year':'2014','end_year':'2018','entry_z':'2.8','exit_z':'0.25','max_active_pairs':'1','pair_risk_pct':'0.035'}),
        ('statarb_cfg_b', {'start_year':'2014','end_year':'2018','entry_z':'2.4','exit_z':'0.20','max_active_pairs':'1','pair_risk_pct':'0.025'}),
        ('statarb_cfg_c', {'start_year':'2014','end_year':'2018','entry_z':'3.2','exit_z':'0.35','max_active_pairs':'1','pair_risk_pct':'0.02'}),
        ('statarb_cfg_d', {'start_year':'2014','end_year':'2018','entry_z':'2.6','exit_z':'0.20','max_active_pairs':'2','pair_risk_pct':'0.025','stop_z':'4.5'}),
    ]

    print('[TUNE] regime IS grid', flush=True)
    regime_rows = []
    for name, p in regime_is:
        r = run_backtest('regime-ensemble-alpha', name, p, 'is')
        regime_rows.append(r)
        runs.append(r)
        print(f"  {name}: net={r['stats']['Net Profit']} sharpe={r['stats']['Sharpe Ratio']}", flush=True)

    print('[TUNE] avwap IS grid', flush=True)
    avwap_rows = []
    for name, p in avwap_is:
        r = run_backtest('anchored-vwap-sleeve', name, p, 'is')
        avwap_rows.append(r)
        runs.append(r)
        print(f"  {name}: net={r['stats']['Net Profit']} sharpe={r['stats']['Sharpe Ratio']}", flush=True)

    print('[TUNE] statarb IS grid', flush=True)
    statarb_rows = []
    for name, p in statarb_is:
        r = run_backtest('statarb-spread-engine', name, p, 'is')
        statarb_rows.append(r)
        runs.append(r)
        print(f"  {name}: net={r['stats']['Net Profit']} sharpe={r['stats']['Sharpe Ratio']}", flush=True)

    regime_best = sorted(regime_rows, key=sort_key, reverse=True)[0]
    avwap_best = sorted(avwap_rows, key=sort_key, reverse=True)[0]
    statarb_best = sorted(statarb_rows, key=sort_key, reverse=True)[0]

    # OOS validation for best configs
    def with_oos(p: Dict[str, str]):
        q = dict(p)
        q['start_year'] = '2019'
        q['end_year'] = '2020'
        return q

    print('[VALIDATE] OOS best configs', flush=True)
    regime_oos = run_backtest('regime-ensemble-alpha', f"{regime_best['scenario']}_oos", with_oos(regime_best['params']), 'oos')
    avwap_oos = run_backtest('anchored-vwap-sleeve', f"{avwap_best['scenario']}_oos", with_oos(avwap_best['params']), 'oos')
    statarb_oos = run_backtest('statarb-spread-engine', f"{statarb_best['scenario']}_oos", with_oos(statarb_best['params']), 'oos')

    runs += [regime_oos, avwap_oos, statarb_oos]

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(runs, indent=2), encoding='utf-8')

    lines = []
    lines.append(f"# Phase 2 Tuning + OOS Validation — {STAMP}")
    lines.append('')
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append('')
    lines.append(f"JSON: `{REPORT_JSON}`")
    lines.append('')

    lines.append('## IS Grid Results')
    lines.append('')
    lines.append('| Project | Scenario | Net Profit | Sharpe | Drawdown | Orders | End Equity | Output |')
    lines.append('|---|---|---:|---:|---:|---:|---:|---|')

    for r in [*regime_rows, *avwap_rows, *statarb_rows]:
        s = r['stats']
        lines.append(
            f"| {r['project']} | {r['scenario']} | {s.get('Net Profit')} | {s.get('Sharpe Ratio')} | {s.get('Drawdown')} | {s.get('Total Orders')} | {s.get('End Equity')} | `{r['output_dir']}` |"
        )

    lines.append('')
    lines.append('## Selected Best-by-IS and OOS Retest')
    lines.append('')
    lines.append('| Project | Selected IS Config | IS Net | OOS Scenario | OOS Net | OOS Sharpe | OOS Drawdown | OOS Output |')
    lines.append('|---|---|---:|---|---:|---:|---:|---|')

    def add_pair(best_row, oos_row):
        lines.append(
            f"| {best_row['project']} | {best_row['scenario']} | {best_row['stats'].get('Net Profit')} | {oos_row['scenario']} | {oos_row['stats'].get('Net Profit')} | {oos_row['stats'].get('Sharpe Ratio')} | {oos_row['stats'].get('Drawdown')} | `{oos_row['output_dir']}` |"
        )

    add_pair(regime_best, regime_oos)
    add_pair(avwap_best, avwap_oos)
    add_pair(statarb_best, statarb_oos)

    REPORT_MD.write_text('\n'.join(lines), encoding='utf-8')
    print(f"REPORT_MD={REPORT_MD}")
    print(f"REPORT_JSON={REPORT_JSON}")


if __name__ == '__main__':
    main()
