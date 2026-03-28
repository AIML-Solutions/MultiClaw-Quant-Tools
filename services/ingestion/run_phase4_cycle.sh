#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$ROOT/infra"
set -a
source .env
if [[ -f .secrets ]]; then source .secrets; fi
set +a

export DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5432/${POSTGRES_DB}"

echo "[phase4] preflight"
python3 "$ROOT/services/ingestion/preflight_phase4.py"

echo "[phase4] running ingestion lanes"
bash "$ROOT/services/ingestion/run_phase3_1_data_lanes.sh"

echo "[phase4] building run ledger"
python3 "$ROOT/lean-cli/scripts/backtests/build_run_ledger.py"

echo "[phase4] refreshing token-efficient research digest"
python3 "$ROOT/research/scripts/update_arxiv_digest.py" --per-topic 15 --top 80

echo "[phase4] syncing dashboard data"
bash "$ROOT/frontend/github-pages/scripts/sync_data.sh"

echo "[phase4] done"
