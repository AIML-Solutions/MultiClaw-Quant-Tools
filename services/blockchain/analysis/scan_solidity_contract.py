#!/usr/bin/env python3
"""
Fast static risk scanner for Solidity contracts.

Heuristic-only pre-screen to identify contracts needing deeper audit.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

RULES = [
    ("delegatecall", r"\.delegatecall\s*\("),
    ("tx_origin", r"tx\.origin"),
    ("selfdestruct", r"selfdestruct\s*\("),
    ("inline_assembly", r"\bassembly\b"),
    ("low_level_call", r"\.call\s*\("),
    ("unchecked_block", r"\bunchecked\s*\{"),
    ("block_timestamp", r"block\.timestamp"),
]


def scan(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings = []
    lines = text.splitlines()

    for name, pat in RULES:
        rx = re.compile(pat)
        for idx, line in enumerate(lines, start=1):
            if rx.search(line):
                findings.append({
                    "rule": name,
                    "line": idx,
                    "snippet": line.strip()[:220],
                })

    severity_map = {
        "delegatecall": "high",
        "tx_origin": "high",
        "selfdestruct": "high",
        "low_level_call": "medium",
        "inline_assembly": "medium",
        "unchecked_block": "medium",
        "block_timestamp": "low",
    }

    for f in findings:
        f["severity"] = severity_map.get(f["rule"], "info")

    score = 0
    for f in findings:
        if f["severity"] == "high":
            score += 3
        elif f["severity"] == "medium":
            score += 2
        elif f["severity"] == "low":
            score += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contract": str(path),
        "findings_count": len(findings),
        "risk_score": score,
        "findings": findings,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("contract", help="path to .sol")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    res = scan(Path(args.contract))

    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=2), encoding="utf-8")
        print(args.out)
    else:
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
