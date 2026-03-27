# Quant Research Library

Curated paper library for building higher-alpha, production-grade systematic strategies.

## Scope

- Execution & microstructure
- Trend/momentum & cross-sectional allocation
- Statistical arbitrage / pairs
- Options, volatility surfaces, 0DTE
- Regime detection and volatility targeting
- Crypto market microstructure and factor effects
- Backtesting methodology, overfitting controls, and evaluation discipline

## Files

- `papers.jsonl` — canonical paper records (one JSON object per line)
- `reading-queue.md` — prioritized reading sequence with implementation mapping
- `query_library.py` — local keyword/topic query helper

## Record Schema (`papers.jsonl`)

Each line:

```json
{
  "id": "unique-slug",
  "title": "Paper title",
  "authors": ["A", "B"],
  "year": 2024,
  "topics": ["options", "volatility"],
  "asset_classes": ["equities", "index options"],
  "url": "https://...",
  "why_it_matters": "short rationale",
  "implementation_notes": "how to convert into strategy research",
  "priority": 1
}
```

Priority scale: **1 = must-read**, 2 = strong, 3 = optional/deep-dive.

## Usage

Search by keyword/topic:

```bash
python3 query_library.py --q "0DTE volatility surface"
python3 query_library.py --topic options --max 10
python3 query_library.py --asset crypto --priority 1
```

## Curation Rules

- Prefer seminal papers and reproducible empirical studies.
- Prefer direct strategy-transfer value over pure theory unless theory underpins pricing/risk.
- Keep `why_it_matters` and `implementation_notes` practical and testable.
- Add only sources with credible provenance (journal, arXiv from known groups, or major conference).
