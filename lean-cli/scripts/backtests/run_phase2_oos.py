#!/usr/bin/env python3
from __future__ import annotations

import glob
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path("/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli")
STAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d_phase2_oos")
REPORT_DIR = ROOT / "docs"
REPORT_MD = REPORT_DIR / f"PHASE2_OOS_VALIDATION_{STAMP}.md"
REPORT_JSON = REPORT_DIR / f"PHASE2_OOS_VALIDATION_{STAMP}.json"


@dataclass
class Run:
    project: str
    scenario: str
    parameters: Dict[str, str]


def runs() -> List[Run]:
    risk_tickers = "SPY,QQQ,IWM,EEM,AAPL,BAC,IBM,GOOG"
    def_tickers = "USO,BNO"
    avwap_tickers = "SPY,QQQ,IWM,EEM,AAPL,BAC,IBM,USO,BNO"

    return [
        Run("baseline-strategy", "baseline_is_2014_2018", {"start_year": "2014", "end_year": "2018", "risk_per_trade": "0.004", "max_positions": "6"}),
        Run("baseline-strategy", "baseline_oos_2019_2020", {"start_year": "2019", "end_year": "2020", "risk_per_trade": "0.004", "max_positions": "6"}),

        Run("regime-ensemble-alpha", "regime_is_2014_2018", {
            "start_year": "2014", "end_year": "2018", "include_crypto": "false",
            "risk_tickers": risk_tickers, "def_tickers": def_tickers, "rebalance_days": "5"
        }),
        Run("regime-ensemble-alpha", "regime_oos_2019_2020", {
            "start_year": "2019", "end_year": "2020", "include_crypto": "false",
            "risk_tickers": risk_tickers, "def_tickers": def_tickers, "rebalance_days": "5"
        }),

        Run("statarb-spread-engine", "statarb_is_2014_2018", {"start_year": "2014", "end_year": "2018"}),
        Run("statarb-spread-engine", "statarb_oos_2019_2020", {"start_year": "2019", "end_year": "2020"}),

        Run("anchored-vwap-sleeve", "avwap_is_2014_2018", {
            "start_year": "2014", "end_year": "2018", "include_crypto": "false", "equity_tickers": avwap_tickers
        }),
        Run("anchored-vwap-sleeve", "avwap_oos_2019_2020", {
            "start_year": "2019", "end_year": "2020", "include_crypto": "false", "equity_tickers": avwap_tickers
        }),

        Run("options-greeks-vix", "options_is_2014", {
            "start_year": "2014", "end_year": "2014", "enable_options": "true", "option_underlying_ticker": "AAPL", "underlying_ticker": "SPY"
        }),
        Run("options-greeks-vix", "options_oos_2015", {
            "start_year": "2015", "end_year": "2015", "enable_options": "true", "option_underlying_ticker": "AAPL", "underlying_ticker": "SPY"
        }),
    ]


def run_one(r: Run) -> Dict:
    out_dir = ROOT / r.project / "backtests" / STAMP / r.scenario
    if out_dir.exists():
        subprocess.run(["rm", "-rf", str(out_dir)], check=True)
    out_dir.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "lean", "backtest", r.project,
        "--output", str(out_dir),
        "--backtest-name", r.scenario,
        "--no-update",
    ]
    for k, v in r.parameters.items():
        cmd += ["--parameter", k, str(v)]

    t0 = datetime.now(timezone.utc)
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    t1 = datetime.now(timezone.utc)

    stats = {}
    files = glob.glob(str(out_dir / "*-summary.json"))
    if files:
        with open(files[0], "r", encoding="utf-8") as f:
            j = json.load(f)
        stats = j.get("statistics", {})

    return {
        "project": r.project,
        "scenario": r.scenario,
        "params": r.parameters,
        "code": p.returncode,
        "duration_sec": round((t1 - t0).total_seconds(), 2),
        "output_dir": str(out_dir),
        "stats": {
            "Total Orders": stats.get("Total Orders"),
            "Net Profit": stats.get("Net Profit"),
            "End Equity": stats.get("End Equity"),
            "Drawdown": stats.get("Drawdown"),
            "Sharpe Ratio": stats.get("Sharpe Ratio"),
            "Sortino Ratio": stats.get("Sortino Ratio"),
            "Total Fees": stats.get("Total Fees"),
        },
    }


def write_reports(rows: List[Dict]):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    md = []
    md.append(f"# Phase 2 OOS Validation — {STAMP}")
    md.append("")
    md.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    md.append("")
    md.append(f"JSON: `{REPORT_JSON}`")
    md.append("")
    md.append("| Project | Scenario | Orders | Net Profit | Sharpe | Drawdown | End Equity | Fees | Output |")
    md.append("|---|---|---:|---:|---:|---:|---:|---:|---|")

    for r in rows:
        s = r["stats"]
        md.append(
            f"| {r['project']} | {r['scenario']} | {s.get('Total Orders')} | {s.get('Net Profit')} | {s.get('Sharpe Ratio')} | {s.get('Drawdown')} | {s.get('End Equity')} | {s.get('Total Fees')} | `{r['output_dir']}` |"
        )

    md.append("")
    md.append("## Notes")
    md.append("- IS vs OOS windows are split by calendar windows to avoid same-period tuning bias.")
    md.append("- These results are based on locally available LEAN sample data coverage.")

    REPORT_MD.write_text("\n".join(md), encoding="utf-8")


def main():
    out = []
    for r in runs():
        print(f"[RUN] {r.project}:{r.scenario}", flush=True)
        res = run_one(r)
        out.append(res)
        print(f"[DONE] {r.project}:{r.scenario} code={res['code']} net={res['stats'].get('Net Profit')} orders={res['stats'].get('Total Orders')}", flush=True)

    write_reports(out)
    print(f"REPORT_MD={REPORT_MD}")
    print(f"REPORT_JSON={REPORT_JSON}")


if __name__ == "__main__":
    main()
