# Reproduction commands

Run from the project root. Install once with `bash scripts/bootstrap.sh`.
The currently active protocol is configs/frozen-protocol.json; the older descriptive
protocol_status in versions.json is historical, not the current execution state.
The frozen source/lock hash must match. The later analysis/ directory is a disclosed
post-hoc source-overlap sensitivity, not a change to model or symbolic methods.

Saved results and figures: `bash scripts/rebuild_study.sh`.
The signed report PDF/source is intentionally private and is not part of this public checkout.
Local archive: `PYTHONPATH=src .env-baseline/bin/python analysis/package_study.py`.

Fresh controlled run (new unique prefix required):

```bash
PYTHONPATH=src .env-baseline/bin/python scripts/run_formal.py --cohort controlled --prefix reproduction-1
```

For real programs, download and sanitize first, using the pinned archive:

```bash
bash scripts/fetch_author_data.sh
PYTHONPATH=src .env-baseline/bin/python scripts/prepare_author_data.py --materials ../private-evaluation/evaluation_materials
PYTHONPATH=src .env-baseline/bin/python scripts/run_formal.py --cohort real --prefix reproduction-1
```

Check existing annotation files before running development review preparation: it
refuses to overwrite student review. The original source/manifests are deterministic;
no model generation script imports evaluator annotations.

To repeat generation on the original fixed twelve subjects with new output names,
run this Python orchestration after setting up the free service:

```bash
PYTHONPATH=src .env-baseline/bin/python - <<'PY'
import json, subprocess, sys
ids=json.load(open('configs/frozen-protocol.json'))['repeat_subjects']
for rep in (1,2):
    # For a new independent experiment use new replicate numbers, e.g. 3 and 4.
    model='runs/new-repeat-%d-model'%rep
    out='runs/new-repeat-%d-neural'%rep
    subprocess.run([sys.executable,'scripts/generate_summaries.py','--baseline-run',
      'runs/reproduction-1-controlled-v1','--out',model,'--stage','formal',
      '--repeat',str(rep),'--sample-id',*ids],check=True)
    subprocess.run([sys.executable,'scripts/replay_effects.py','--baseline-run',
      'runs/reproduction-1-controlled-v1','--out',out,'--methods','S1','N0','N1',
      '--summaries',model,'--sample-id',*ids],check=True)
PY
```

Existing replicate identities reuse exact cached responses. A new replicate number
causes actual new inference and consumes the shared formal token cap; do not call
cache replay a fresh stochastic generation. The report concerns replicates 0/1/2.
The raw model cache is private; exported records contain responses and request hashes
but no executable cache payload. To rerun purely offline symbolic inference, use
`replay_effects.py` with the existing saved batch and a locally regenerated S0 run.

The script run_formal.py --cohort all uses the original fixed repeat output names;
it is suitable for the initial empty run layout, not an overwrite of packaged runs.
The explicit cohort commands above support later reproduction without deleting
original evidence.
