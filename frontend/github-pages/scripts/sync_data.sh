#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
DOCS="$ROOT/lean-cli/docs"
OUT="$ROOT/frontend/github-pages/data"

mkdir -p "$OUT"

cp "$DOCS/PHASE3_BACKTEST_MATRIX_2026-03-28_phase3_matrix.json" "$OUT/PHASE3_BACKTEST_MATRIX.json"
cp "$DOCS/PHASE3_BACKTEST_MATRIX_2026-03-28_phase3_matrix.md" "$OUT/PHASE3_BACKTEST_MATRIX.md"

cp "$DOCS/PHASE3_WALKFORWARD_2026-03-28_phase3_walkforward.json" "$OUT/PHASE3_WALKFORWARD.json"
cp "$DOCS/PHASE3_WALKFORWARD_2026-03-28_phase3_walkforward.md" "$OUT/PHASE3_WALKFORWARD.md"

cp "$DOCS/PHASE3_SLEEVE_ALLOCATOR_2026-03-28_phase3_allocator.json" "$OUT/PHASE3_ALLOCATOR.json"
cp "$DOCS/PHASE3_SLEEVE_ALLOCATOR_2026-03-28_phase3_allocator.md" "$OUT/PHASE3_ALLOCATOR.md"

cp "$DOCS/PHASE3_METHOD_VALIDITY_REPORT_2026-03-28.md" "$OUT/PHASE3_METHOD_VALIDITY.md"
cp "$DOCS/PHASE3_DATA_QUALITY_AUDIT.md" "$OUT/PHASE3_DATA_QUALITY_AUDIT.md"

if [[ -f "$DOCS/RUN_LEDGER.json" ]]; then
  cp "$DOCS/RUN_LEDGER.json" "$OUT/RUN_LEDGER.json"
fi
if [[ -f "$DOCS/RUN_LEDGER.md" ]]; then
  cp "$DOCS/RUN_LEDGER.md" "$OUT/RUN_LEDGER.md"
fi

if [[ -f "$ROOT/research/data/ARXIV_DIGEST.md" ]]; then
  cp "$ROOT/research/data/ARXIV_DIGEST.md" "$OUT/ARXIV_DIGEST.md"
fi

if [[ -f "$ROOT/services/ingestion/sample_tradier_paper_snapshot.json" ]]; then
  cp "$ROOT/services/ingestion/sample_tradier_paper_snapshot.json" "$OUT/PAPER_SNAPSHOT.json"
fi

echo "Synced dashboard data to $OUT"
