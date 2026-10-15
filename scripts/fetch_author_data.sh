#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
EVALUATION_ROOT=${1:-"$PROJECT_ROOT/../private-evaluation"}
if [[ ! -d "$EVALUATION_ROOT/.git" ]]; then
  git clone https://github.com/malusamayo/GitHubAPI-Crawler.git "$EVALUATION_ROOT"
fi
git -C "$EVALUATION_ROOT" checkout --detach 3aec5fa09788d6659c6e1eac79cdc503340d9694
cd "$PROJECT_ROOT"
PYTHONPATH=src .env-baseline/bin/python scripts/prepare_author_data.py --materials "$EVALUATION_ROOT/evaluation_materials"
