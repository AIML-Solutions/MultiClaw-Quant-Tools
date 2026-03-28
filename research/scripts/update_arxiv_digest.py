#!/usr/bin/env python3
"""
Token-efficient ArXiv digest builder.

- Uses only metadata + abstract snippets (no LLM calls)
- Scores papers by recency + keyword density + topic relevance
- Writes jsonl + markdown digest
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ARXIV_API = "http://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}


def load_topics(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_topic(query: str, max_results: int) -> str:
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = ARXIV_API + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")


def days_since(ts: str) -> int:
    try:
        t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return 9999
    now = dt.datetime.now(dt.timezone.utc)
    return max(0, (now - t).days)


def keyword_score(text: str, keywords: list[str]) -> int:
    t = text.lower()
    return sum(t.count(k.lower()) for k in keywords)


def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def score_entry(entry: dict, topic_name: str) -> float:
    text = f"{entry['title']} {entry['summary']}"
    common_kw = [
        "alpha",
        "backtest",
        "execution",
        "volatility",
        "regime",
        "options",
        "order flow",
        "microstructure",
        "portfolio",
        "crypto",
        "on-chain",
    ]
    topic_bonus = {
        "trend_momentum": ["momentum", "trend"],
        "options_vol_surface": ["implied volatility", "surface", "greeks", "0dte"],
        "statarb_pairs": ["pairs", "cointegration", "mean reversion"],
        "execution_microstructure": ["execution", "slippage", "order book"],
        "crypto_market_structure": ["crypto", "blockchain", "on-chain"],
        "portfolio_regime": ["regime", "portfolio", "risk"],
    }

    recency_days = days_since(entry["published"])
    recency = max(0.0, 1.0 - (recency_days / 365.0))
    kw = keyword_score(text, common_kw)
    tkw = keyword_score(text, topic_bonus.get(topic_name, []))

    # Compact deterministic score to avoid LLM token spend.
    return round(1.8 * recency + 0.25 * kw + 0.5 * tkw, 4)


def parse_feed(xml_text: str, topic_name: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    out = []

    for e in root.findall("atom:entry", NS):
        title = normalize_space(e.findtext("atom:title", default="", namespaces=NS))
        summary = normalize_space(e.findtext("atom:summary", default="", namespaces=NS))
        published = e.findtext("atom:published", default="", namespaces=NS)
        updated = e.findtext("atom:updated", default="", namespaces=NS)
        arxiv_id = (e.findtext("atom:id", default="", namespaces=NS) or "").split("/")[-1]

        authors = []
        for a in e.findall("atom:author", NS):
            authors.append(a.findtext("atom:name", default="", namespaces=NS))

        categories = []
        for c in e.findall("atom:category", NS):
            term = c.attrib.get("term")
            if term:
                categories.append(term)

        row = {
            "id": arxiv_id,
            "topic": topic_name,
            "title": title,
            "summary": summary,
            "published": published,
            "updated": updated,
            "authors": authors,
            "categories": categories,
            "url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
        }
        row["score"] = score_entry(row, topic_name)
        out.append(row)

    return out


def dedup_best(rows: list[dict]) -> list[dict]:
    best = {}
    for r in rows:
        k = r.get("id") or (r.get("title", "")[:120])
        if not k:
            continue
        if k not in best or r["score"] > best[k]["score"]:
            best[k] = r
    return sorted(best.values(), key=lambda x: x["score"], reverse=True)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_markdown(path: Path, rows: list[dict], top_n: int) -> None:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    lines = [
        "# ArXiv Quant Digest",
        "",
        f"Generated: {now}",
        "",
        "Token-efficient mode: metadata scoring only (no LLM summarization).",
        "",
        "| Rank | Topic | Score | Published | Title | URL |",
        "|---:|---|---:|---|---|---|",
    ]

    for i, r in enumerate(rows[:top_n], start=1):
        title = r["title"].replace("|", "\\|")
        lines.append(
            f"| {i} | {r['topic']} | {r['score']:.3f} | {r['published'][:10]} | {title} | {r['url']} |"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topics", default=str(Path(__file__).resolve().parents[1] / "arxiv" / "topics.json"))
    ap.add_argument("--per-topic", type=int, default=20)
    ap.add_argument("--top", type=int, default=80)
    ap.add_argument("--jsonl", default=str(Path(__file__).resolve().parents[1] / "data" / "arxiv_digest.jsonl"))
    ap.add_argument("--md", default=str(Path(__file__).resolve().parents[1] / "data" / "ARXIV_DIGEST.md"))
    args = ap.parse_args()

    topics = load_topics(Path(args.topics))
    all_rows = []

    for name, query in topics.items():
        try:
            xml = fetch_topic(query, args.per_topic)
            rows = parse_feed(xml, name)
            all_rows.extend(rows)
        except Exception as exc:
            print(f"[warn] topic {name} failed: {exc}")

    merged = dedup_best(all_rows)
    write_jsonl(Path(args.jsonl), merged)
    write_markdown(Path(args.md), merged, args.top)

    print(f"rows={len(merged)}")
    print(f"jsonl={args.jsonl}")
    print(f"md={args.md}")


if __name__ == "__main__":
    main()
