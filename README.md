# Contextual preprocessing effects for Python leakage analysis

Code and experimental evidence for the CS6215 individual project on parameter-sensitive
cross-sample dependencies in custom Python preprocessing functions. The author's
name, student identifier, and signed report (PDF and sources) are not distributed.

## Methods

- **S0** reproduces the pinned upstream interprocedural symbolic analyzer.
- **S1** adds deterministic contextual effects using parameter, rank and state evidence.
- **N0** injects saved model proposals after structural/reference checks.
- **N1** additionally requires semantic agreement with S1's derivable effects.

N0/N1 use the same actual saved model responses. S1 has all deterministic knowledge
available to N1. Strict N1 cannot establish a neural accuracy advantage over S1.
Upstream already supports function calls; wrapper support itself is not a contribution.

## Results and limits

The experiment includes 16 controlled development programs, 32 scheduled controlled
tests, 21 real notebook candidates, 128 paired syntactic variants, and three
generations on 12 selected subjects. The scheduled controlled-test F1 scores are
S0 0.786, S1 0.839, N0 0.800, and N1 0.839.

Two test programs duplicate development source. Original runs are retained; a
disclosed post-hoc whole-family exclusion leaves 28 controlled subjects and 112
variants. Those variants are paired observations, not independent projects.
Four real subjects fail the frozen frontend environment. Unknown, error and timeout
are never counted as no leakage. All recorded label/scope judgments are author-approved;
event-only and scope-limited conclusions retain null program labels.

See `results/study/`, `docs/final_review.md`, `docs/decisions.md`, and `docs/ai_use_log.md`.
Implementation, prompts, experiment orchestration and writing involved AI assistance.
Public review records identify the reviewer by role, with boolean labels unchanged.

## Rebuild saved results

Linux x86_64; Python 3.8.20, Node 16.20.2, Pyright 1.1.188, Souffle 2.4.1.

```bash
bash scripts/bootstrap.sh
bash scripts/rebuild_study.sh
```

The rebuild uses saved predictions and response-only model evidence, without private
notebook files, API credentials or new requests. It generates numerical results,
figures and temporary table fragments in the ignored `report/` directory; the signed
report and its source are not included. Forty unit tests and seven baseline regressions
passed in the original environment; independent reproduction is documented in
`docs/baseline_reproduction.md`.

For fresh controlled analysis with an existing authorized free SoCLaaS service:

```bash
PYTHONPATH=src .env-baseline/bin/python scripts/run_formal.py \
  --cohort controlled --prefix reproduction-1
```

Use a unique output prefix. See `docs/reproduction_commands.md` and
`docs/soclaas_setup.md` for model setup, repeat runs and real-data downloads.
TLS SNI and certificate checks retain the original SoCLaaS hostname when tunnelling.
No paid fallback or model training is used. Never commit credentials.

Baseline and Pyright commits are `a7d038bfec6b8ddbe21d87dde54b806aecdd79f7` and
`e3d7d9c44ac69fa6bc66bb8a47377fcec034e503`. The original tool is
[leakage-analysis](https://github.com/malusamayo/leakage-analysis), accompanying
[Data Leakage in Notebooks](https://arxiv.org/abs/2209.03345).

## Public packaging

```bash
PYTHONPATH=src .env-baseline/bin/python analysis/package_study.py
```

This creates `../CS6215_public_code_artifact.zip` from tracked public files with a
SHA-256 manifest. The original private history and signed report remain local.
See `PUBLIC_RELEASE.md` for the publication boundary.
