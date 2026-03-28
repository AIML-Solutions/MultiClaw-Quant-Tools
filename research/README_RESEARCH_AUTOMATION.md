# Research Automation (Token-Efficient)

## Goal
Continuously harvest high-signal research without burning LLM tokens on fullpaper summarization.

## Pipeline
1. Pull ArXiv metadata for quant topics.
2. Score entries using deterministic heuristics (recency + keyword relevance).
3. Store ranked digest as JSONL + Markdown.
4. Use LLM only on shortlisted papers when implementing strategy upgrades.

## Run

```bash
python3 research/scripts/update_arxiv_digest.py --per-topic 25 --top 80
```

Outputs:
- `research/data/arxiv_digest.jsonl`
- `research/data/ARXIV_DIGEST.md`

## Notes
- This is intentionally model-free to preserve token budget.
- Extend `research/arxiv/topics.json` as strategy scope grows.
