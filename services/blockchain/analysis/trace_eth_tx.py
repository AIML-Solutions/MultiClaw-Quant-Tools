#!/usr/bin/env python3
"""
Ethereum transaction tracer (RPC-first, public-node compatible).

- Retrieves tx + receipt
- Attempts debug_traceTransaction when available
- Emits normalized JSON summary
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime, timezone


def rpc_call(url: str, method: str, params: list):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read().decode("utf-8"))
    if "error" in resp:
        raise RuntimeError(resp["error"])
    return resp.get("result")


def h2i(x):
    if x is None:
        return None
    try:
        return int(x, 16)
    except Exception:
        return None


def summarize(tx: dict, receipt: dict, trace: dict | None):
    logs = receipt.get("logs", []) if receipt else []

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tx_hash": tx.get("hash") if tx else None,
        "from": tx.get("from") if tx else None,
        "to": tx.get("to") if tx else None,
        "nonce": h2i(tx.get("nonce")) if tx else None,
        "block_number": h2i(tx.get("blockNumber")) if tx else None,
        "gas": h2i(tx.get("gas")) if tx else None,
        "gas_price_wei": h2i(tx.get("gasPrice")) if tx else None,
        "value_wei": h2i(tx.get("value")) if tx else None,
        "status": h2i(receipt.get("status")) if receipt else None,
        "gas_used": h2i(receipt.get("gasUsed")) if receipt else None,
        "effective_gas_price_wei": h2i(receipt.get("effectiveGasPrice")) if receipt else None,
        "contract_address": receipt.get("contractAddress") if receipt else None,
        "logs_count": len(logs),
        "logs_topics": [l.get("topics", []) for l in logs[:20]],
        "trace_available": trace is not None,
        "trace": trace,
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tx_hash", help="0x... transaction hash")
    ap.add_argument("--rpc", default="https://cloudflare-eth.com", help="Ethereum JSON-RPC URL")
    ap.add_argument("--out", default="", help="optional output json path")
    args = ap.parse_args()

    tx = rpc_call(args.rpc, "eth_getTransactionByHash", [args.tx_hash])
    if tx is None:
        raise SystemExit("Transaction not found")

    receipt = rpc_call(args.rpc, "eth_getTransactionReceipt", [args.tx_hash])

    trace = None
    try:
        trace = rpc_call(args.rpc, "debug_traceTransaction", [args.tx_hash, {"tracer": "callTracer"}])
    except Exception:
        # Public RPCs often disable debug methods; this is expected.
        trace = None

    out = summarize(tx, receipt, trace)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print(args.out)
    else:
        print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
