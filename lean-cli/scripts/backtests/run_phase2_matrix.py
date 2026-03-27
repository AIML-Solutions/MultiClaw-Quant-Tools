#!/usr/bin/env python3
from __future__ import annotations

import glob
import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


ROOT = Path("/home/aimls-dtd/.openclaw-nemoclaw/workspace/projects/quantconnect/lean-cli")
STAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d_phase2_matrix")
REPORT_DIR = ROOT / "docs"
REPORT_PATH = REPORT_DIR / f"PHASE2_BACKTEST_MATRIX_{STAMP}.md"
JSON_PATH = REPORT_DIR / f"PHASE2_BACKTEST_MATRIX_{STAMP}.json"


@dataclass
class Scenario:
    project: str
    name: str
    parameters: Dict[str, str]


def scenarios() -> List[Scenario]:
    common_regime = {
        "start_year": "2018",
        "end_year": "2021",
        "include_crypto": "false",
        "risk_tickers": "SPY,QQQ,IWM,EEM,AAPL,BAC,IBM,GOOG",
        "def_tickers": "USO,BNO",
    }
    common_avwap = {
        "start_year": "2018",
        "end_year": "2021",
        "include_crypto": "false",
        "equity_tickers": "SPY,QQQ,IWM,EEM,AAPL,BAC,IBM,USO,BNO",
    }

    return [
        Scenario("baseline-strategy", "baseline_core", {
            "start_year": "2018", "end_year": "2021", "risk_per_trade": "0.004", "max_positions": "6"
        }),
        Scenario("baseline-strategy", "baseline_defensive", {
            "start_year": "2018", "end_year": "2021", "risk_per_trade": "0.003", "max_positions": "4", "max_position_notional": "0.14"
        }),
        Scenario("baseline-strategy", "baseline_aggressive", {
            "start_year": "2018", "end_year": "2021", "risk_per_trade": "0.006", "max_positions": "8", "max_position_notional": "0.22"
        }),

        Scenario("regime-ensemble-alpha", "regime_core", {
            **common_regime, "rebalance_days": "5", "target_portfolio_vol": "0.14"
        }),
        Scenario("regime-ensemble-alpha", "regime_low_turnover", {
            **common_regime, "rebalance_days": "10", "max_turnover_per_rebalance": "0.20", "target_portfolio_vol": "0.12"
        }),
        Scenario("regime-ensemble-alpha", "regime_risk_tight", {
            **common_regime, "rebalance_days": "5", "target_portfolio_vol": "0.10", "max_drawdown": "0.08", "hard_stop_drawdown": "0.12"
        }),

        Scenario("statarb-spread-engine", "statarb_core", {
            "start_year": "2018", "end_year": "2021"
        }),
        Scenario("statarb-spread-engine", "statarb_conservative", {
            "start_year": "2018", "end_year": "2021", "entry_z": "3.1", "pair_risk_pct": "0.025", "max_active_pairs": "1", "min_edge_z": "1.5"
        }),
        Scenario("statarb-spread-engine", "statarb_active", {
            "start_year": "2018", "end_year": "2021", "entry_z": "2.5", "pair_risk_pct": "0.045", "max_active_pairs": "2", "stop_z": "4.5"
        }),

        Scenario("anchored-vwap-sleeve", "avwap_core", {
            **common_avwap
        }),
        Scenario("anchored-vwap-sleeve", "avwap_defensive", {
            **common_avwap, "risk_per_trade": "0.003", "max_positions": "4", "max_position_weight": "0.15"
        }),
        Scenario("anchored-vwap-sleeve", "avwap_aggressive", {
            **common_avwap, "risk_per_trade": "0.005", "max_positions": "6", "max_position_weight": "0.24", "trail_atr_mult": "2.2"
        }),

        Scenario("options-greeks-vix", "options_core", {
            "start_year": "2014", "end_year": "2015", "enable_options": "true", "option_underlying_ticker": "AAPL", "underlying_ticker": "SPY"
        }),
        Scenario("options-greeks-vix", "options_tighter_greeks", {
            "start_year": "2014", "end_year": "2015", "enable_options": "true", "option_underlying_ticker": "AAPL", "underlying_ticker": "SPY",
            "target_delta_low_vol": "0.30", "target_delta_high_vol": "0.20", "max_abs_delta_exposure": "250", "max_abs_vega_exposure": "4500"
        }),
        Scenario("options-greeks-vix", "options_fallback_only", {
            "start_year": "2014", "end_year": "2015", "enable_options": "false", "fallback_equity_mode": "true", "underlying_ticker": "SPY", "option_underlying_ticker": "AAPL"
        }),
    ]


def run_backtest(s: Scenario) -> Dict:
    out_dir = ROOT / s.project / "backtests" / STAMP / s.name
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    if out_dir.exists():
        subprocess.run(["rm", "-rf", str(out_dir)], check=True)

    cmd = [
        "lean", "backtest", s.project,
        "--output", str(out_dir),
        "--backtest-name", s.name,
        "--no-update",
    ]
    for k, v in s.parameters.items():
        cmd += ["--parameter", k, str(v)]

    started = datetime.now(timezone.utc)
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    ended = datetime.now(timezone.utc)

    summary_candidates = glob.glob(str(out_dir / "*-summary.json"))
    summary = {}
    if summary_candidates:
        with open(summary_candidates[0], "r", encoding="utf-8") as f:
            summary = json.load(f)

    stats = summary.get("statistics", {}) if isinstance(summary, dict) else {}
    data_quality = {}

    log_candidates = glob.glob(str(out_dir / "*-log.txt"))
    if log_candidates:
        try:
            with open(log_candidates[0], "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            for line in text.splitlines():
                if "DATA USAGE:: Failed data requests percentage" in line:
                    data_quality["failed_data_requests_pct"] = line.split("percentage", 1)[-1].strip().lstrip(":").strip()
                elif "DATA USAGE:: Total data requests" in line:
                    data_quality["total_data_requests"] = line.split("requests", 1)[-1].strip().lstrip(":").strip()
                elif "DATA USAGE:: Failed data requests " in line and "percentage" not in line:
                    data_quality["failed_data_requests"] = line.split("requests", 1)[-1].strip().lstrip(":").strip()
        except Exception:
            pass

    return {
        "project": s.project,
        "scenario": s.name,
        "parameters": s.parameters,
        "status_code": p.returncode,
        "started": started.isoformat(),
        "ended": ended.isoformat(),
        "duration_sec": round((ended - started).total_seconds(), 2),
        "output_dir": str(out_dir),
        "stats": {
            "Total Orders": stats.get("Total Orders"),
            "Net Profit": stats.get("Net Profit"),
            "End Equity": stats.get("End Equity"),
            "Drawdown": stats.get("Drawdown"),
            "Sharpe Ratio": stats.get("Sharpe Ratio"),
            "Sortino Ratio": stats.get("Sortino Ratio"),
            "Win Rate": stats.get("Win Rate"),
            "Profit-Loss Ratio": stats.get("Profit-Loss Ratio"),
            "Total Fees": stats.get("Total Fees"),
            "Portfolio Turnover": stats.get("Portfolio Turnover"),
        },
        "data_quality": data_quality,
        "stderr_tail": "\n".join((p.stderr or "").splitlines()[-20:]),
        "stdout_tail": "\n".join((p.stdout or "").splitlines()[-20:]),
    }


def write_report(results: List[Dict]):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    lines = []
    lines.append(f"# Phase 2 Backtest Matrix — {STAMP}")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append(f"JSON artifact: `{JSON_PATH}`")
    lines.append("")
    lines.append("| Project | Scenario | Orders | Net Profit | Sharpe | Drawdown | End Equity | Fees | Data Fail % | Output |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---|")

    for r in results:
        s = r["stats"]
        dq = r.get("data_quality", {})
        fail_pct = dq.get("failed_data_requests_pct", "n/a")
        lines.append(
            "| {project} | {scenario} | {orders} | {net} | {sharpe} | {dd} | {end} | {fees} | {fail} | `{out}` |".format(
                project=r["project"],
                scenario=r["scenario"],
                orders=s.get("Total Orders", "n/a"),
                net=s.get("Net Profit", "n/a"),
                sharpe=s.get("Sharpe Ratio", "n/a"),
                dd=s.get("Drawdown", "n/a"),
                end=s.get("End Equity", "n/a"),
                fees=s.get("Total Fees", "n/a"),
                fail=fail_pct,
                out=r["output_dir"],
            )
        )

    lines.append("")
    lines.append("## Sanity Checks")
    lines.append("")
    for r in results:
        if r["status_code"] != 0:
            lines.append(f"- ❌ `{r['project']}:{r['scenario']}` exited with code {r['status_code']}")
        elif str(r["stats"].get("Total Orders", "0")) in ["0", "0.0", "None", "n/a"]:
            lines.append(f"- ⚠️ `{r['project']}:{r['scenario']}` had zero orders")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    all_results: List[Dict] = []

    for s in scenarios():
        print(f"[RUN] {s.project}:{s.name}", flush=True)
        res = run_backtest(s)
        all_results.append(res)
        print(
            f"[DONE] {s.project}:{s.name} code={res['status_code']} "
            f"orders={res['stats'].get('Total Orders')} net={res['stats'].get('Net Profit')} "
            f"dur={res['duration_sec']}s",
            flush=True,
        )

    write_report(all_results)
    print(f"REPORT_MD={REPORT_PATH}")
    print(f"REPORT_JSON={JSON_PATH}")


if __name__ == "__main__":
    main()
