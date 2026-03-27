#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_records(path: Path):
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def score_record(rec, q_terms, topic, asset, max_priority):
    if max_priority is not None and int(rec.get("priority", 99)) > max_priority:
        return -1

    if topic:
        topics = [t.lower() for t in rec.get("topics", [])]
        if topic.lower() not in topics:
            return -1

    if asset:
        assets = [a.lower() for a in rec.get("asset_classes", [])]
        if asset.lower() not in assets:
            return -1

    text = " ".join([
        rec.get("title", ""),
        " ".join(rec.get("authors", [])),
        " ".join(rec.get("topics", [])),
        " ".join(rec.get("asset_classes", [])),
        rec.get("why_it_matters", ""),
        rec.get("implementation_notes", ""),
    ]).lower()

    if not q_terms:
        return 1

    hits = sum(1 for t in q_terms if t in text)
    return hits


def main():
    p = argparse.ArgumentParser(description="Query quant paper library")
    p.add_argument("--path", default="papers.jsonl")
    p.add_argument("--q", default="", help="keyword query")
    p.add_argument("--topic", default="")
    p.add_argument("--asset", default="")
    p.add_argument("--priority", type=int, default=None)
    p.add_argument("--max", type=int, default=15)
    args = p.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"Library not found: {path}")
        return

    q_terms = [x.strip().lower() for x in args.q.split() if x.strip()]
    recs = load_records(path)

    ranked = []
    for r in recs:
        s = score_record(r, q_terms, args.topic, args.asset, args.priority)
        if s < 0:
            continue
        ranked.append((s, r))

    ranked.sort(key=lambda x: (x[0], -int(x[1].get("priority", 99))), reverse=True)

    if not ranked:
        print("No matching records.")
        return

    for i, (_, r) in enumerate(ranked[: args.max], start=1):
        print(f"[{i}] {r.get('title')} ({r.get('year')})")
        print(f"    id: {r.get('id')}")
        print(f"    topics: {', '.join(r.get('topics', []))}")
        print(f"    assets: {', '.join(r.get('asset_classes', []))}")
        print(f"    priority: {r.get('priority')}")
        print(f"    url: {r.get('url')}")
        print(f"    why: {r.get('why_it_matters')}")
        print(f"    impl: {r.get('implementation_notes')}")
        print()


if __name__ == "__main__":
    main()
