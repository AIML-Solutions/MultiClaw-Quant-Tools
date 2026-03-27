#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys
import urllib.parse
from datetime import datetime, timezone

import requests

VERSION = "onchain-lite 0.1.0"
CG = "https://api.coingecko.com/api/v3"
LLAMA_CHAINS = "https://api.llama.fi/v2/chains"
POLY = "https://gamma-api.polymarket.com/markets"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def out(obj, as_json: bool):
    if as_json:
        print(json.dumps(obj, indent=2))
    else:
        if isinstance(obj, str):
            print(obj)
        else:
            print(json.dumps(obj, indent=2))


def cmd_test(args):
    checks = {}
    for name, url in {
        "coingecko": f"{CG}/ping",
        "defillama": LLAMA_CHAINS,
        "polymarket": f"{POLY}?active=true&closed=false&limit=2",
    }.items():
        try:
            r = requests.get(url, timeout=12)
            checks[name] = {"ok": r.ok, "status": r.status_code}
        except Exception as e:
            checks[name] = {"ok": False, "error": str(e)}
    out({"generated_utc": now_iso(), "version": VERSION, "checks": checks}, args.json)


def cmd_price(args):
    tok = args.token.lower().strip()
    r = requests.get(
        f"{CG}/simple/price",
        params={"ids": tok, "vs_currencies": "usd", "include_24hr_change": "true", "include_market_cap": "true"},
        timeout=15,
    )
    r.raise_for_status()
    j = r.json().get(tok)
    if not j:
        out({"error": f"token_not_found:{tok}"}, True)
        return
    payload = {
        "generated_utc": now_iso(),
        "token": tok,
        "priceUsd": j.get("usd"),
        "priceChange24hPct": j.get("usd_24h_change"),
        "marketCapUsd": j.get("usd_market_cap"),
    }
    out(payload, args.json)


def cmd_markets(args):
    r = requests.get(
        f"{CG}/coins/markets",
        params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": args.limit,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h",
        },
        timeout=20,
    )
    r.raise_for_status()
    rows = [
        {
            "symbol": x.get("symbol", "").upper(),
            "name": x.get("name"),
            "price": x.get("current_price"),
            "mcap": x.get("market_cap"),
            "volume24h": x.get("total_volume"),
            "change24hPct": x.get("price_change_percentage_24h"),
        }
        for x in r.json()
    ]
    out({"generated_utc": now_iso(), "top": rows}, args.json)


def cmd_gas(args):
    chain = (args.chain or "ethereum").lower()
    if chain != "ethereum":
        out({"generated_utc": now_iso(), "chain": chain, "note": "gas oracle currently implemented for ethereum only in onchain-lite"}, args.json)
        return
    # Public endpoint, may be rate-limited.
    url = "https://api.etherscan.io/api"
    try:
        r = requests.get(url, params={"module": "gastracker", "action": "gasoracle"}, timeout=12)
        j = r.json()
        res = j.get("result") or {}
        payload = {
            "generated_utc": now_iso(),
            "chain": "ethereum",
            "safe": res.get("SafeGasPrice"),
            "propose": res.get("ProposeGasPrice"),
            "fast": res.get("FastGasPrice"),
            "suggestBaseFee": res.get("suggestBaseFee"),
        }
        out(payload, args.json)
    except Exception as e:
        out({"generated_utc": now_iso(), "chain": "ethereum", "error": str(e)}, True)


def cmd_polymarket_sentiment(args):
    topic = (args.topic or "ethereum").lower().strip()
    blocked = ["nhl", "nba", "nfl", "mlb", "premier league", "world cup", "stanley cup", "fifa"]
    r = requests.get(POLY, params={"active": "true", "closed": "false", "limit": args.limit}, timeout=25)
    r.raise_for_status()
    markets = r.json() if isinstance(r.json(), list) else []
    rows = []
    vals = []
    for m in markets:
        q = str(m.get("question") or "")
        ql = q.lower()
        if topic not in ql:
            continue
        if any(b in ql for b in blocked):
            continue
        prices = m.get("outcomePrices")
        try:
            if isinstance(prices, str):
                prices = json.loads(prices)
            yes = float(prices[0])
            no = float(prices[1])
        except Exception:
            continue
        vol = float(m.get("volume") or 0)
        liq = float(m.get("liquidity") or 0)
        edge = abs(yes - no)
        vals.append(yes)
        rows.append({
            "question": q,
            "slug": m.get("slug"),
            "yes": round(yes, 3),
            "no": round(no, 3),
            "volume": vol,
            "liquidity": liq,
            "edge": round(edge, 3),
        })
    rows.sort(key=lambda x: (x["volume"], x["liquidity"]), reverse=True)
    tone = "mixed"
    avg_yes = (sum(vals) / len(vals)) if vals else None
    if avg_yes is not None:
        tone = "bullish" if avg_yes > 0.58 else ("bearish" if avg_yes < 0.42 else "mixed")
    out({"generated_utc": now_iso(), "topic": topic, "markets": rows[:20], "avg_yes": avg_yes, "tone": tone}, args.json)


def cmd_chains(args):
    r = requests.get(LLAMA_CHAINS, timeout=20)
    r.raise_for_status()
    rows = []
    for c in r.json():
        rows.append({
            "name": c.get("name"),
            "tvl": c.get("tvl"),
            "tokenSymbol": c.get("tokenSymbol"),
        })
    rows.sort(key=lambda x: x.get("tvl") or 0, reverse=True)
    out({"generated_utc": now_iso(), "chains": rows[: args.limit]}, args.json)


def build():
    p = argparse.ArgumentParser(prog="onchain")
    p.add_argument("--json", action="store_true", help="json output")
    p.add_argument("--version", action="store_true")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("test")
    s.set_defaults(fn=cmd_test)

    s = sub.add_parser("price")
    s.add_argument("token")
    s.set_defaults(fn=cmd_price)

    s = sub.add_parser("markets")
    s.add_argument("-l", "--limit", type=int, default=10)
    s.set_defaults(fn=cmd_markets)

    s = sub.add_parser("gas")
    s.add_argument("--chain", default="ethereum")
    s.set_defaults(fn=cmd_gas)

    s = sub.add_parser("chains")
    s.add_argument("-l", "--limit", type=int, default=10)
    s.set_defaults(fn=cmd_chains)

    s = sub.add_parser("polymarket")
    ss = s.add_subparsers(dest="p_cmd")
    p2 = ss.add_parser("sentiment")
    p2.add_argument("topic")
    p2.add_argument("-l", "--limit", type=int, default=600)
    p2.set_defaults(fn=cmd_polymarket_sentiment)

    return p


def main():
    parser = build()
    args = parser.parse_args()
    if args.version:
        print(VERSION)
        return 0
    if not getattr(args, "cmd", None):
        parser.print_help()
        return 0
    fn = getattr(args, "fn", None)
    if fn is None:
        parser.print_help()
        return 1
    fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
