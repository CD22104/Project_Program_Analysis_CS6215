# Project execution rules

Read STATUS.md and docs/decisions.md before continuing. The user authorizes local
implementation, analysis, testing, and report preparation. Publishing, sending
messages, and course submission require a separate instruction.

Keep S0 at the pinned upstream versions. Record compatibility patches separately
from analysis changes. Never execute analyzed programs or model-generated code.
Analyzer and model inputs contain sanitized source and API specifications only;
annotations, notebook outputs, upstream HTML, and baseline predictions belong to
the evaluator. N0 and N1 replay identical saved model responses. S1 receives all
deterministic knowledge available to N1. Report unknown/error/timeout separately.

Never invent results, human review, or student contributions. Current review approvals
are recorded in docs/student_decisions.json; retain event-only and scope-limited
judgments without inferring binary labels. Course PDFs and notebooks
with unconfirmed redistribution licenses stay outside the public artifact.
No model calls until credentials, service authorization, and cost/budget are known.
Do not print secrets. Update STATUS.md, docs/decisions.md, and docs/ai_use_log.md
after each stage. Do not change memory files.
