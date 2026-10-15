# Decisions

## A1 — scope and authorization (2026-10-14)

Follow the supplied preprocessing-leakage definition: evaluation information must
affect training representations. Test-only refitting is a separate protocol issue.
Upstream PreProcessingLeak uses a disjunction allowing flow to train OR test;
therefore preserve its raw predictions and report the scope mismatch explicitly.
Do not silently redefine S0.

The course PDFs specify the assignment, not execution authorization. Local work is
authorized by the user. Public release and submission are deferred.

## A2 — isolation

Private handoff and author evaluation materials are siblings of the public-artifact
directory. Each baseline run gets a fresh copied input and separate facts directory.
Use Python 3.8 first; retain all attempted environment failures. API calls await
service and budget information. Offline interface fixtures are never experiments.

## A3 — research contribution

The baseline already propagates actual/formal arguments and returns. The proposed
contribution is parameter-sensitive effect summaries and evidence-checked symbolic
integration, not function encapsulation. Gains from added deterministic rules must
also be available to S1. Student confirmation of hypotheses remains pending.

## B1 — development evidence and provisional split (2026-10-15)

Twenty-four constructed semantic families are prepared. Families F00–F07 were
predeclared as development cases before their runs; F08–F23 remain unexecuted and
unfrozen. This replaces the proposed random 8/16 family split with a disclosed
semantic split to include all six requested pilot contrasts. It was an AI-assisted
engineering decision, not a student-confirmed research decision. Formal conclusions
must discuss possible template dependence and cannot call this a randomized split.

The initial real-data screen selects parseable code with explicit split, fit, and
predict/score calls, independent of labels and method predictions. It produces 21
candidates, including five seeded development candidates. Being a candidate is not
equivalent to confirmed scope or label validity. Sources and licenses remain
unconfirmed. The first raw CSV row inspected during format diagnosis belongs to
an excluded notebook, not a held-out candidate.

## C1 — integration and proof boundary

Reuse upstream SSA, typed facts, two-call-site contexts, pointer/data-flow relations,
and Datalog solver. Candidate effects attach to the precise primitive invocation
inside a custom function, while the existing interprocedural solver composes their
impact on parameters and returns. We do not claim a new general call-graph engine
or a monolithic LLM classifier of complete functions.

S1 resolves direct import aliases, propagates constants and receiver kinds through
actual/formal bindings, and infers bounded axis effects. The derived Datalog adds
EffectAtCall, suppresses only a proved row-local rowset effect at its call/context,
and injects new reductions before re-solving. Other taints remain. Fits retain
upstream object propagation. Transform state is accepted only with a unique prior
fit identified through points-to and invocation ordering; refits are unsupported.

N1 currently requires equality with independently derivable effects. Thus S1 and
verified N1 should agree on covered calls. This is an explicit strict-verification
design and a limitation for demonstrating neural accuracy gains. N0 can accept a
structurally valid but semantically false safe summary; adversarial unit fixtures
show N1 rejects it, but fixtures are not experimental model outputs.

## C2 — development failures

The first derived Datalog used `input` as a field name, a reserved token in Soufflé.
All failed pilot-v1 solver outputs are retained. The integration was fixed and
replayed on the same saved frontends. Later revisions added actual/formal receiver
typing, candidate relevance, and explicit object-state checks. Pilot-v2 through
pilot-v4 preserve each iteration. These are development iterations, not final tests.

## D1 — zero-cost service and current connectivity

The user explicitly requires no spending and provided a personal SoCLaaS config.
Only that free service is enabled. Its config is outside the artifact, mode 600.
On 2026-10-15, DNS resolved but TCP 443 timed out. No authentication response or
live model summary has been received. Optional loopback SSH forwarding preserves
the original TLS hostname and verification. No paid fallback or purchase is allowed.

## C3 — bounded parameter proofs (2026-10-15)

Inspection of the installed, pinned library source/signatures showed that negative
axes cannot be interpreted uniformly: NumPy wraps them, while pandas and scale
reject them. Quantile has q before axis. The shared specification now records
these facts, scale flags, and conservative handling of unsupported arguments/mutations.
Both-disabled scale statistics are row-local; unresolved options remain unknown.
The summary binds the primitive-specification hash. All 34 unit checks pass;
pilot-v6 and real-pilot-v3 replay the change with unchanged development predictions.

## B2 — real development review, not relabeling

The private packet records five code inspections. Full-data means in
real_38101a98cc8f support a proposed primary-task positive, while S1 is unknown.
real_926b37074ebc selects features using full-data target correlation before
splitting despite an author pre=N label; this is a proposed revision for student
review. LabelEncoder and text-vectorizer cases need scope decisions. No label
changes or real accuracy claims are made.

A diagnostic matching only nb_1743 encountered two dates and displayed one extra
author row from the already excluded real_0d964f20c22e (syntax error). No reserved
candidate label was exposed. The persisted review script requires the full
date-plus-notebook path; its output only contains development cases. Original
labels remain private and do not enter prompts.

## E1 — review artifact and report preparation

The English report is a development draft with actual symbolic results and empty
neural columns. It records the strict-verifier limitation and pending student
contributions. Official acmart class/source and bibliography style are bundled with
their license; course PDFs, real notebook code, credentials and model prompt bodies
are excluded from the public review archive. A local ZIP is preparation, not
publication/submission. Saved-result rebuild and fresh-install checks are recorded
individually rather than inferred from success in the existing environment.

## E2 — paired evaluation and clean-install checks

Execution coverage counts all scheduled subjects even when labels are unavailable;
confusion matrices use only labelled successful results. N0/N1 comparisons reject
different batch hashes, and all method comparisons reject different source hashes.
The study evaluator keeps stable wrong variants visible and excludes unknown/error
from binary repeat agreement. Forty unit checks pass; study fixtures are not actual
model/variant/repetition experiments. Repeat subjects are selected by a fixed source
identifier within each seeded family, without consulting labels.

The first fresh bootstrap encountered default-channel Conda terms despite explicit
conda-forge package locks. The script now overrides channels to conda-forge only;
no terms were accepted for unrelated channels. The failure log is retained.
The extracted archive rebuilt the saved table/figure and seven-page report; the
separate full dependency bootstrap is checked independently.

The clean dependency bootstrap completed, with an exact pip lock and identical
Pyright package locks. Running the current source there reproduced all seven
regressions, forty unit checks and sixteen development predictions. The consolidated
record and complete copied runs are under runs/. Current controlled tables use
this clean run. Protocol checks now reject post-freeze code/lock/cohort changes;
analysis checks source bytes against manifests, and S0 rejects local semantic
modifications to the pinned upstream source.

The author crawler's gather-nbs.py assigns notebook numbers from per-date nbs.txt
lists, while gather_info.py uses those lists to recover repository identities.
The released evaluation materials contain broad repository lists but not the
required per-date mapping files. Thus three independent source repositories have
not been established; notebook count is not a substitute. No provenance is invented.

## D2 — distinguish network evidence from policy

On 2026-10-15 the public SoCLaaS gateway page was reachable through web research.
It explicitly restricts Portal/docs access to NUS, without stating the same for
the API. The server's fresh authenticated model-list request still timed out.
Instructions therefore start with a local-computer connectivity test and use its
existing NUS access plus SSH forwarding if needed. VPN absence is a hypothesis,
not an established diagnosis. No server routes or authentication configuration were
changed, and no model inference was attempted.

## D3 — live service, development evidence, and freeze decision

On 2026-10-15 the student established an SSH reverse tunnel on 127.0.0.1:9443.
Authenticated model discovery and inference succeeded through that tunnel. The
URL and HTTP hostname remain soclaas-api.comp.nus.edu.sg; the TLS socket supplies
that hostname as SNI with default trusted-root and hostname verification. The
private config remains mode 600. The explicit catalogue model qwen3-coder-next was
selected before inference or held-out evaluation; no paid fallback is permitted.

The first development request used 2,050 provider-reported tokens. The full
controlled development generation reused it and made thirteen further requests
(27,165 tokens). N0 and N1 replay the same fourteen proposals: N0 rejected one;
N1 rejected four, including rule-inconsistent effects. Controlled primary F1 is
S0=.800, S1=1.000, N0=.875, N1=1.000 with provisional labels. Five real development
programs required nineteen further proposals (40,329 tokens); S1/N1 retain one
unknown while N0 returns five no-findings. Higher execution coverage is not proof
of correctness. No prompt or semantic rule was tuned after these live pilots.

The fixed implementation, shared spec, prompt, model-service config, cohort hashes,
720-second timeout, and seeded twelve-family repeat subset will be frozen before
formal execution. Reporting/export scripts were completed beforehand because the
implementation digest covers Python scripts too. Human label/method review is a
separate status; pending review does not stop authorized local experiments.

The student supplied the name Project author and NUS identifier [withheld], and explicitly
approved revising real_926b37074ebc to a positive on 2026-10-15 because full-data
target-correlation selection precedes splitting. Original author pre=N is retained.
Only this case is marked student_reviewed; no approval of other cases is inferred.
Response-only model records will be exported for public review; original request
bodies remain private because they may contain unlicensed real notebook code.

## E3 — frozen test execution and disclosed source overlap

The frozen protocol digest is 9edcff10256b98989b80158acc38a6c7fbceaf97f735ec6d210621292e9022cf.
All four modes completed on 32 scheduled controlled test programs. The real cohort
completed with four baseline import failures, preserved without dependency changes;
S1/N1 additionally retain one unknown. Frozen methods and prompts remain unchanged.

Two controlled cache hits triggered a source-hash audit. F22's negative is identical
to F03's development negative, and F23's positive is identical to F03's development
positive. This is a construction/splitting defect, not independent held-out evidence.
The original 32-program cohort and all results remain preserved and disclosed.
A post-hoc sensitivity analysis excludes *whole* F22/F23 families using source
hash equality alone, yielding 28 base programs and 112 paired variants. No method,
prompt, prediction or label is changed. This subset is not described as predeclared.

The new evaluator-only analysis/evaluate_integrity.py and Bash rebuild entry point
are added after freeze and versioned separately; the frozen Python implementation
and orchestration scripts are unchanged. The original implementation guard still
passes. This extension documents a data-integrity defect rather than silently
rewriting the frozen experiment. A separate exploratory normalized-AST audit flags
four real test--test similarities and no cross-partition pair above .25, but cannot
establish repository or semantic independence. No real cohort changes are made.

## E4 — additional student review

On 2026-10-15 Project author explicitly confirmed positive preprocessing events in
real_621d7038c43a, real_1859b28c0b0f, real_4aabfe0b5836, and real_38101a98cc8f.
Together with real_926b37074ebc, five positive program labels now have student review.
Original author fields are retained. Other labels, including negative events and
constructed examples, remain pending. The student also endorsed the interpretation
boundary: current N1 cannot establish greater accuracy than S1; the contribution
is the contextual interface and analysis of summary errors/verification/coverage.
The frozen protocol's pending-review fields are historical snapshots; current
review decisions are in docs/student_decisions.json and evaluator annotations.

## E5 — completed original cohorts, robustness and cost

All scheduled cohorts and repetitions completed. Original controlled S0/S1/N0/N1
F1 is .786/.839/.800/.839 with provisional labels. Variant S1/N1 have 3/32 flips
for each wrapper depth and none for rename/comments. N0 has 4/32 rename, 1/32 comment,
3/32 wrap1 and 2/32 wrap2 flips. S0 is stable but wrong on six pairs of each kind.
The source-disjoint sensitivity is explicitly post-hoc, excludes whole F22/F23,
and reports 28 base programs plus 112 variants. Neither view establishes real-world
accuracy or independent template generalization.

Three generations agree for all twelve selected predictions, with eleven subjects
having candidates and thirteen full-summary triples identical. Overall inference
uses 212 actual requests and 445,534 reported tokens, no failed requests or missing
usage; monetary expenditure is zero. Twelve cache-hit references are distinct from
new inference, including the two disclosed development/test source collisions.

The independently installed environment reproduces all 128 predictions and selected
raw evidence fields for a fresh 32-program baseline run with saved model batches.
The English report includes five student-reviewed positives, original errors and
unknowns, controlled misses/false alarms, verifier rejection, instability and cost.
Bibliographic metadata was checked against the original paper and pinned commits.
No publication or course submission has occurred.

The extracted public archive successfully rebuilt all 18 numerical JSON/CSV files
and generated TeX outputs without private sources or API credentials. The final
layout is nine pages (eight main, one references). Secret scans of the prospective
Git files and ZIP matched no actual key value; archive manifests matched all bytes.
Final archive verification is stored beside the ZIP so its checksum is not circular.

The completed real review packet covers all sixteen reserved candidates after
prediction generation. It distinguishes two further positive proposals in failed
runs (global scalers) from approved labels, and marks image/categorical/row-filtering
scope questions explicitly. No additional program labels were approved or supplied
to model generation. The evaluator still uses only the five confirmed positives.

## E6 — personal participation and AI disclosure approved

On 2026-10-15 Project author explicitly confirmed that the proposed personal participation
and AI-use account is accurate and approved recording it. Student participation is
limited to specifying the topic/comparison constraints, requiring free resources,
configuring SoCLaaS/tunnel access, reviewing five real positives, and endorsing the
strict-N1 conclusion boundary. Implementation, prompts, experimental orchestration
and initial report drafting remain disclosed as AI assistance. This approval does
not approve other labels, independent implementation authorship, publication or
course submission. The report and review checklist now reflect this completed review.

## E7 — report pagination and explicit GitHub publication authorization

On 2026-10-15 the student requested that AI Usage Statement and Artifact and Review
Procedure start on a new page and explicitly authorized pushing the reviewed project
to https://github.com/CD22104/Project_Program_Analysis_CS6215. This instruction
satisfies the separate publication requirement; it does not authorize course
submission or messages to others. The existing GitHub token is read only from the
private mode-600 configuration and is never placed in remote URLs, Git history,
repository files or logs. The target is public and initially has no Git refs.

The two sections now occupy separate columns on page 8. The report remains nine
pages (eight main plus one references) and includes the repository link. Remaining
labels keep their pending-review status. The frozen implementation digest is
unchanged. The prepublication audit scanned all existing Git objects and historical
paths plus current tracked files: no configured credential or forbidden private
file was found. Initial publication and an anonymous-clone rebuild are the next
verification steps; their completion will be recorded separately.

The initial push succeeded at commit [private-history-reference-omitted].
An anonymous clone verified public access and contained no private notebook sources
or model request cache. Using the already independently bootstrapped dependencies,
the actual GitHub copy rebuilt all 18 numerical JSON/CSV files and four generated
TeX tables identically, passed the frozen implementation hash check, and compiled
the nine-page PDF with both requested sections on page 8. This check did not repeat
dependency installation or make model calls. Raw rebuild/compile logs and structured
verification are in runs/environment/github-*. Course submission remains pending.

## E8 — final author confirmation and formal academic report

On 2026-10-15 the student explicitly confirmed all recorded review results and
requested a final paper, removal of the draft subtitle and duplicate location lines,
and a self-contained explanation of background, motivation, method definitions and
limitations. The existing controlled/variant boolean labels are unchanged and now
marked approved. Real binary proposals are approved as recorded: seven positive
programs and six negative programs across the 21 candidates. Eight other judgments
remain event-only or scope-limited with null program labels. Blanket confirmation
is not evidence of an independent second annotation, whole-program safety for an
event-only negative, or independent human assessment of every model summary.

The earlier five-positive annotation subset is preserved in
data/annotations/review-history/real-reviewed-before-final-approval.json. Original
dataset fields and frozen prediction files are retained. Private full source/author
review packets record the same approval. Only evaluator labels and reporting changed;
no prompts, analysis code, primitive rules or model inputs were modified. The frozen
implementation digest still equals
9edcff10256b98989b80158acc38a6c7fbceaf97f735ec6d210621292e9022cf.

The final report defines S0/S1/N0/N1 in text and a comparison table, adds a concrete
axis-sensitive example and effect-selection equations, and distinguishes labels,
execution coverage and semantic coverage. It retains the source-overlap defect,
path-feasibility false alarm, unsupported effects, missing-import failures and the
strict-N1 equivalence boundary. A stale workflow caption describing model inference
as unexercised was corrected to match actual saved API evidence. AI assistance and
the author's responsibilities remain explicit. The affiliation shows only the
university; the institution's name still includes Singapore.

A separately versioned analysis/finalize_report.py runs after the frozen rebuild
script. It overrides obsolete historical label-status text, regenerates the figure
from unchanged counts, and reports a labelled-subset table for the eleven reserved
real programs (five positive, six negative). Each method detects two of the five
known positives, including unsuccessful analyses in that denominator (recall .400).
S0/N0 have eight binary outcomes in this subset; S1/N1 have seven plus one unknown.
This table does not assign binary labels to the other five reserved candidates.
The final PDF has ten pages: nine main/appendix pages and one references page.
AI Usage Statement and Artifact and Reproduction Procedure share page nine.

## E9 — restricted public release

After automatic approval review rejected the broader final-report push, the student
explicitly authorized publication with new restrictions: do not publish the personal
name, student identifier or report. The final signed report remains local. Public
code/evidence must therefore be exported to a separate sanitized checkout, with
report sources/PDF omitted and annotation reviewer names replaced by an anonymous
author role. The private scientific record retains original attribution. Earlier
public commits contained the report and identity, so a clean public history is needed
to remove those files from the branch's reachable history. Preserve the full local
history before changing the public branch and use a lease against the verified
remote head. Never push this private checkout to GitHub directly.
