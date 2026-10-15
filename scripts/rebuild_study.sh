#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src
mkdir -p report
.env-baseline/bin/python scripts/rebuild_all.py --require-formal
.env-baseline/bin/python analysis/evaluate_integrity.py
.env-baseline/bin/python analysis/report_extras.py
.env-baseline/bin/python analysis/finalize_report.py
