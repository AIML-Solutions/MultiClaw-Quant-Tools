# Quant GitHub Pages Dashboard

Static interactive dashboard for market/portfolio/strategy visibility.

## What it shows
- Strategy matrix and walk-forward reports
- Sleeve allocator outputs
- Methodology and data quality docs
- Paper-trading snapshot JSON (if present)

## Local preview

```bash
cd frontend/github-pages
python3 -m http.server 8080
# open http://localhost:8080
```

## Refresh dashboard data

From repo root:

```bash
bash frontend/github-pages/scripts/sync_data.sh
```

This copies latest docs JSON/MD artifacts into `frontend/github-pages/data/`.

## GitHub Pages
- Set repository Pages source to `frontend/github-pages` (or publish this folder via Actions).
- Dashboard works with static JSON/MD files only; no backend required.
