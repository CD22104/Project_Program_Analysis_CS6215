# Baseline reproduction evidence

The baseline is pinned to a7d038bfec6b8ddbe21d87dde54b806aecdd79f7 with custom
Pyright e3d7d9c44ac69fa6bc66bb8a47377fcec034e503. Its Python analyzer and Datalog
semantics are unchanged in S0. Upstream bootstrap updated three Node lockfiles;
the exact dependency-only patch is in `third_party/patches/`.

Actual environment: Python 3.8.20, Node 16.20.2, Soufflé 2.4.1, NumPy 1.24.4,
pandas 1.5.3, scikit-learn 1.3.2. Soufflé's official Ubuntu 20.04 binary is extracted
locally. Its SHA-512 matches the release checksum. A separate Conda libffi 3.3
environment supplies the required libffi.so.7 ABI. System packages are unchanged.

Attempts and outcomes:

- Conda-forge `souffle=2.4` was unavailable; Python/Node were installed separately.
- The official Soufflé binary initially failed to load libffi.so.7. An attempted
  Ubuntu libffi download returned 404; the isolated Conda library solved it.
- Sandboxed Pyright could not spawn Python (`spawnSync python3 EPERM`), yielding
  unresolved imports and `Unknown.fit`. These results were retrospectively marked
  errors and retained in `runs/baseline-smoke`, including original output.
- With Python spawning permitted, upstream test0–test4 exactly matched their
  asserted method sets: three LogisticRegression.fit positives and two negatives.
  Evidence: `runs/baseline-smoke-unsandboxed/checks.json` and per-program logs.
- The original nb_481597 function regression has missing/obsolete imports,
  including pandas.tools.plotting. Its failure is retained; it is not presented as
  a passing regression. A minimal statistics-return helper in the controlled
  probe reports LogisticRegression.fit for its positive and no finding for its
  train-only negative. Both use unmodified upstream interprocedural analysis.

The adapter requires a success marker, valid type JSON, fresh transformed source,
fact inputs, all three preprocessing relations, and valid field counts. Exit zero
is insufficient. Missing imports are treated as environment failures. Each run
uses a unique input copy and kills the complete process group on outer timeout.

Upstream PreProcessingLeak contains train-OR-test influence. The task requires
training influence. The evaluator projection preserves original output and joins
train dependence, evaluation-source overlap, and exact reduction contexts. It
does not change S0's rules or reinterpret an empty result as a safety proof.

## Final development reruns (2026-10-15)

`runs/baseline-final-smoke/checks.json` contains seven passing checks: test0–test4
and two minimal positive/negative helper wrappers. This does not erase the legacy
notebook failure. `runs/pilot-v5` is the fresh 16-program S0/S1 run after extending
the dependency lock; `runs/pilot-v6` reuses those S0 facts for the latest proof rules.

`runs/real-pilot-v1` retains all five initial import failures. After adding pinned
plotting/statistical/NLP libraries, `runs/real-pilot-v2` completed all five S0 runs.
`runs/real-pilot-v3` replays the latest S1: four no_finding and one unknown. These
are statuses, not accuracy metrics against reviewed event labels.

The original environment was assembled by recorded individual commands.
`bootstrap.sh` encodes them for a fresh location. Merely providing that script does
not establish that a full clean installation was tested; any such verification
is recorded separately below.

### Clean installation actually completed

The review archive was extracted into `/tmp/cs6215-clean-repro-k1h36sf9/leakage-project`.
Its first bootstrap failed on default Conda channel terms. Restricting channels to
conda-forge fixed the bootstrap without accepting those unrelated terms. Logs are
`runs/environment/clean-bootstrap-attempt1.log` and `clean-bootstrap.log`.

The corrected script created fresh Python/Node and libffi environments, installed
locked Python libraries, cloned and built the pinned Pyright, and verified/extracted
Soufflé. Pip freeze and all three Pyright package lockfiles exactly match the main
environment. Current project source was copied into that isolated installation;
40 tests, seven regressions and the sixteen-program S0/S1 pilot then passed, with
identical source hashes and predictions to the prior development run.

Complete run evidence was copied back to `runs/clean-reproduction-smoke` and
`runs/clean-reproduction-controlled`. The consolidated check is
`runs/environment/clean-reproduction-check.json`. The extracted archive also rebuilt
the saved metrics/figure and compiled the seven-page report. No model request,
held-out program analysis, notebook execution, purchase or publication was involved.

### Final four-method reproduction

After protocol freeze, the frozen source, configurations, controlled manifests and
saved actual model batches were copied into the independently installed environment
above. All 32 scheduled controlled programs received a fresh S0 run, followed by
S1/N0/N1 replay. The 128 predictions match the original experiment on source hashes,
raw status, task-projected status, batch hash, raw preprocessing rows, projected
relations, verifier checks and unknown reasons. No new model request was made.
Evidence: runs/environment/final-clean-reproduction-check.json, its console log,
and runs/final-reproduction-controlled plus runs/final-reproduction-neural.
This reproduces the original scheduled cohort, including its disclosed F22/F23
source overlap; reproduction does not repair data independence.

### Public artifact reconstruction

The response-only public review archive was extracted without real notebook source
or private model-cache request bodies. Using the installed locked interpreter,
`bash scripts/rebuild_study.sh` reproduced all 18 numerical JSON/CSV files and all
four generated report tables/text files exactly. The bundled ACM source compiled
the nine-page report: eight pages of main text including appendix/AI disclosure,
plus one reference page. The initial page-count expectation was eight total before
final layout edits; verification uses the actual nine-page output. This is within
the course limit. Raw verification logs remain in runs/environment; the final ZIP
has a separate external checksum/verification JSON to avoid self-referential hashes.
