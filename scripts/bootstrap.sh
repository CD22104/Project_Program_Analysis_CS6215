#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"
CONDA_BIN=${CONDA_EXE:-}
if [[ -z "$CONDA_BIN" ]]; then
  CONDA_BIN=$(command -v conda || true)
fi
if [[ -z "$CONDA_BIN" && -x "$HOME/miniconda3/bin/conda" ]]; then
  CONDA_BIN="$HOME/miniconda3/bin/conda"
fi
if [[ -z "$CONDA_BIN" ]]; then
  echo 'Install a Conda-compatible environment manager first.' >&2
  exit 1
fi
mkdir -p runs/environment .tools/downloads .tools/souffle third_party
if [[ ! -x .env-baseline/bin/python ]]; then
  "$CONDA_BIN" create -y --override-channels -c conda-forge -p "$PROJECT_ROOT/.env-baseline" --file configs/conda-baseline-linux-64.lock
fi
if [[ ! -f .env-ffi/lib/libffi.so.7 ]]; then
  "$CONDA_BIN" create -y --override-channels -c conda-forge -p "$PROJECT_ROOT/.env-ffi" --file configs/conda-ffi-linux-64.lock
fi
.env-baseline/bin/python -m pip install -r configs/requirements-baseline.lock
if [[ ! -d third_party/leakage-analysis/.git ]]; then
  git clone https://github.com/malusamayo/leakage-analysis.git third_party/leakage-analysis
fi
git -C third_party/leakage-analysis checkout --detach a7d038bfec6b8ddbe21d87dde54b806aecdd79f7
git -C third_party/leakage-analysis submodule update --init --recursive
export PATH="$PROJECT_ROOT/.env-baseline/bin:$PATH"
(
  cd third_party/leakage-analysis/pyright
  if git apply --check "$PROJECT_ROOT/third_party/patches/pyright-bootstrap-lockfiles.patch"; then
    git apply "$PROJECT_ROOT/third_party/patches/pyright-bootstrap-lockfiles.patch"
  elif ! git apply --reverse --check "$PROJECT_ROOT/third_party/patches/pyright-bootstrap-lockfiles.patch"; then
    echo 'Unexpected Pyright dependency changes; inspect before continuing.' >&2
    exit 1
  fi
  npm ci
  cd packages/pyright
  npm run build
)
curl -fsSL https://github.com/souffle-lang/souffle/releases/download/2.4.1/x86_64-ubuntu-2004-souffle-2.4.1-Linux.deb -o .tools/downloads/souffle.deb
.env-baseline/bin/python - <<'PY'
import hashlib,json
from pathlib import Path
metadata=json.loads(Path('configs/tool-downloads.json').read_text())
assert hashlib.sha512(Path('.tools/downloads/souffle.deb').read_bytes()).hexdigest()==metadata['sha512']
PY
dpkg-deb -x .tools/downloads/souffle.deb .tools/souffle
PYTHONPATH=src .env-baseline/bin/python scripts/audit_environment.py
echo 'Environment ready. Run baseline_smoke.py in a fresh output directory.'
