#!/usr/bin/env python3
"""
Bitcoin transaction tracer via Blockstream public API.

- Fetches tx details
- Traces spend path for each output up to configurable depth
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime, timezone


API = "https://blockstream.info/api"


def get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "quant-tracer/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def trace_outspend(txid: str, vout: int, depth: int):
    out = {
        "txid": txid,
        "vout": vout,
        "depth": depth,
        "spent": None,
        "spending_txid": None,
        "children": [],
    }
    if depth <= 0:
        return out

    sp = get_json(f"{API}/tx/{txid}/outspend/{vout}")
    out["spent"] = sp.get("spent")
    out["spending_txid"] = sp.get("txid")

    if sp.get("spent") and sp.get("txid"):
        next_tx = get_json(f"{API}/tx/{sp['txid']}")
        for idx, _ in enumerate(next_tx.get("vout", [])):
            out["children"].append(trace_outspend(sp["txid"], idx, depth - 1))

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("txid")
    ap.add_argument("--depth", type=int, default=1)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    tx = get_json(f"{API}/tx/{args.txid}")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "txid": args.txid,
        "status": tx.get("status"),
        "vin_count": len(tx.get("vin", [])),
        "vout_count": len(tx.get("vout", [])),
        "vout_trace": [],
    }

    for i, _ in enumerate(tx.get("vout", [])):
        summary["vout_trace"].append(trace_outspend(args.txid, i, args.depth))

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(args.out)
    else:
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
