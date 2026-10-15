"""Re-run upstream Datalog with call/context-specific, typed effect facts."""
import csv
import shutil
import subprocess
from pathlib import Path
from .baseline import BASELINE, environment
from .common import ROOT, write_json

DECLARATIONS = '''
// CS6215 effect interface: caller context is essential for wrapper constants.
.decl EffectAtCall(invo:Invocation, ctx:Context, kind:symbol, srcIdx:number, dstIdx:number)
.input EffectAtCall
.decl SuppressRowEffect(invo:Invocation, ctx:Context, label:symbol)
SuppressRowEffect(i, c, "rowset") :- EffectAtCall(i, c, "row_preserving", _, _).
'''
INJECTION = '''
// Add effects independently of original warnings, then re-solve all data flow.
TaintStarts(var, ctx, "rowset"),
TaintStartsTarget(target, ctx, var, ctx, invo, meth, "rowset") :-
    EffectAtCall(invo, ctx, "cross_row_reduce", srcIdx, dstIdx),
    CallGraphEdge(invo, ctx, meth, _),
    ActualParam(srcIdx, invo, var), ActualReturn(dstIdx, invo, target).
TaintStarts(var, ctx, "rowset"),
TaintStartsTarget(target, ctx, var, ctx, invo, meth, "rowset") :-
    EffectAtCall(invo, ctx, "fit_state", srcIdx, dstIdx),
    CallGraphEdge(invo, ctx, meth, _),
    ActualParam(srcIdx, invo, var), ActualParam(dstIdx, invo, target).
'''

def derived_datalog():
    text = (BASELINE / "src/main.dl").read_text()
    old = "    ActualParam(fromIdx, invo, var).\n\n/* -----------------------------\nPre-processing leak detection"
    new = "    ActualParam(fromIdx, invo, var),\n    !SuppressRowEffect(invo, callerCtx, label).\n\n/* -----------------------------\nPre-processing leak detection"
    if text.count(old) != 1:
        raise ValueError("Pinned integration point changed")
    return text.replace(old, new).replace("// ---- inputs ----", DECLARATIONS + "\n// ---- inputs ----") + INJECTION

def solve(baseline_dir, out, effect_rows, timeout=720):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    fact_dir = out / "facts"
    fact_dir.mkdir()
    for p in (Path(baseline_dir) / "work/input-fact").glob("*.facts"):
        shutil.copy2(p, fact_dir / p.name)
    # Facts are built exclusively from schema-checked values and allowlisted IDs.
    with (fact_dir / "EffectAtCall.facts").open("w", newline="") as f:
        csv.writer(f, delimiter="\t", lineterminator="\n").writerows(effect_rows)
    program = out / "analysis.dl"
    program.write_text(derived_datalog())
    cmd = ["souffle", str(program.resolve()), "-F", str(fact_dir.resolve()), "-D", str(fact_dir.resolve())]
    with (out / "solver.log").open("w") as log:
        p = subprocess.run(cmd, env=environment(), stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
    if p.returncode:
        raise RuntimeError("Derived solver failed; see solver.log")
    with (fact_dir / "PreProcessingLeak.csv").open(newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    if any(len(r) != 4 for r in rows):
        raise RuntimeError("Invalid derived output arity")
    return rows
