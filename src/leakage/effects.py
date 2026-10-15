"""Context-specific effect inference over the unchanged upstream facts.

The model receives code, bound constants, API knowledge, and legal references.
It never receives labels, upstream predictions, telemetry, or notebook output.
"""
import ast
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from .common import ROOT, digest

UNKNOWN = object()
KINDS = {"row_preserving", "cross_row_reduce", "fit_state", "apply_state", "unknown"}
SPECS = json.loads((ROOT / "specs/primitives.json").read_text())

def primitive_effect(canonical, rank, axis, parameters):
    """A deliberately bounded API proof, shared by S1 and N1.

    Parameters have already been bound at the invocation. Missing parameters use
    the pinned API's defaults; explicit unresolved values do not use defaults.
    """
    tail = canonical.split('.')[-1]
    owner = canonical.split('.')[-2] if '.' in canonical else ''
    scale = canonical == 'sklearn.preprocessing.scale'
    numpy = canonical == 'numpy.' + tail or owner == 'ndarray'
    pandas = owner in ('DataFrame', 'Series')
    if not (scale or numpy or pandas) or rank not in (1, 2):
        return 'unknown', 'unresolved input rank or primitive identity'
    if parameters.get('_unsupported_arguments'):
        return 'unknown', 'arguments outside the reviewed primitive subset'
    # The effect interface currently models return dependencies, not arbitrary
    # writes through out=, inplace buffers, or data-dependent reduction options.
    if parameters.get('out') is not None or parameters.get('where') is not None:
        return 'unknown', 'out/where dependence is outside the reviewed subset'
    if parameters.get('overwrite_input', False) is not False:
        return 'unknown', 'possible mutation through overwrite_input'
    if tail == 'quantile':
        q = parameters.get('q', UNKNOWN)
        if type(q) not in (int, float) or not 0 <= q <= 1:
            return 'unknown', 'quantile probability is not a reviewed scalar constant'
    if scale:
        if parameters.get('copy', True) is not True:
            return 'unknown', 'possible mutation through scale(copy=...)'
        if type(axis) is not int or axis not in (0, 1) or axis >= rank:
            return 'unknown', 'invalid or unresolved scale axis for this rank'
        mean, std = parameters.get('with_mean', True), parameters.get('with_std', True)
        if type(mean) is not bool or type(std) is not bool:
            return 'unknown', 'unresolved scale centering/variance options'
        if not mean and not std:
            return 'row_preserving', 'both scale statistics are disabled'
    elif pandas:
        # pandas 1.5 rejects negative axis numbers. None for these reducers is
        # the axis-0 default, unlike NumPy's all-axis reduction.
        if axis is None:
            axis = 0
        if type(axis) is str:
            axis = {'index': 0, 'rows': 0, 'columns': 1}.get(axis, UNKNOWN)
        if type(axis) is not int or axis < 0 or axis >= rank:
            return 'unknown', 'invalid or unresolved pandas axis for this rank'
    elif axis is not None:
        if type(axis) is not int or axis < -rank or axis >= rank:
            return 'unknown', 'invalid or unresolved NumPy axis for this rank'
        axis %= rank
    if axis is None or axis == 0:
        return 'cross_row_reduce', 'reduction includes sample axis 0'
    return 'row_preserving', 'reduction excludes sample axis 0'

def rows(directory, name):
    p = Path(directory) / name
    if not p.exists():
        return []
    with p.open(newline="") as f:
        return list(csv.reader(f, delimiter="\t"))

class Frontend:
    def __init__(self, run_dir):
        self.run_dir = Path(run_dir)
        self.fact_dir = self.run_dir / "work/input-fact"
        self.source = (self.run_dir / "work/input.py").read_text()
        self.ir = (self.run_dir / "work/input.py.ir.py").read_text()
        self.source_sha = digest(self.source)
        self.tree = ast.parse(self.ir)
        self.types = dict(rows(self.fact_dir, "VarType.facts"))
        self.calls = {i: (m, f) for i, m, f in rows(self.fact_dir, "Invoke.facts")}
        self.actual = {(i, int(k)): v for k, i, v in rows(self.fact_dir, "ActualParam.facts")}
        self.keywords = {(i, k): v for k, i, v in rows(self.fact_dir, "ActualKeyParam.facts")}
        self.returns = {(i, int(k)): v for k, i, v in rows(self.fact_dir, "ActualReturn.facts")}
        self.formals = {(m, int(k)): v for k, m, v in rows(self.fact_dir, "FormalParam.facts")}
        self.formal_returns = {(m, int(k)): v for k, m, v in rows(self.fact_dir, "FormalReturn.facts")}
        self.edges = rows(self.fact_dir, "CallGraphEdge.csv")
        self.contexts = {"[, ]"} | {c for _, c, _, _ in self.edges} | {c for _, _, _, c in self.edges}
        self.lines = {i: int(l) for i, l in rows(self.fact_dir, "InvokeLineno.facts")}
        self.ast_calls = {n.lineno: n for n in ast.walk(self.tree) if isinstance(n, ast.Call)}
        self.functions = {n.name: n for n in self.tree.body if isinstance(n, ast.FunctionDef)}
        self.aliases = {}
        for n in ast.walk(self.tree):
            if isinstance(n, ast.ImportFrom):
                for a in n.names:
                    self.aliases[a.asname or a.name] = (n.module or "") + "." + a.name
        self.constants = defaultdict(set)
        self.ranks = defaultdict(set)
        self.kinds = defaultdict(set)
        self.objects = defaultdict(set)
        for name, rank in (("AssignIntConstant.facts", int), ("AssignBoolConstant.facts", lambda s: s == "True"),
                           ("AssignStrConstant.facts", str), ("AssignFloatConstant.facts", float)):
            for var, value in rows(self.fact_dir, name):
                for ctx in self.contexts:
                    self.constants[var, ctx].add((rank(value).__class__.__name__, rank(value)))
        # Precise DataFrame/Series types provide rank. Unknown/union/ndarray do not.
        for var, typ in self.types.items():
            rank = 2 if typ in ("pandas.DataFrame", "DataFrame") else 1 if typ in ("pandas.Series", "Series") else None
            if rank:
                for ctx in self.contexts:
                    self.ranks[var, ctx].add(rank)
                    self.kinds[var, ctx].add("DataFrame" if rank == 2 else "Series")
            if (typ[5:] if typ.startswith("Self@") else typ) in SPECS["stateful_classes"]:
                for ctx in self.contexts:
                    self.objects[var, ctx].add((typ[5:] if typ.startswith("Self@") else typ))
        # Context-bounded copy and actual/formal propagation. A set with more than
        # one value is unresolved. Never select one branch's convenient value.
        for _ in range(100):
            changed = False
            pairs = [((to, ctx), (src, ctx)) for to, src in rows(self.fact_dir, "AssignVar.facts") for ctx in self.contexts]
            for i, caller, method, callee in self.edges:
                for (m, k), var in self.formals.items():
                    if m == method:
                        actual = self.actual.get((i, k)) or self.keywords.get((i, var))
                        if actual:
                            pairs.append(((var, callee), (actual, caller)))
                for (m, k), var in self.formal_returns.items():
                    actual = self.returns.get((i, k))
                    if m == method and actual:
                        pairs.append(((actual, caller), (var, callee)))
            for mapping in (self.constants, self.ranks, self.kinds, self.objects):
                for to, src in pairs:
                    old = len(mapping[to]); mapping[to].update(mapping[src])
                    changed |= old != len(mapping[to])
            # Reviewed shape-preserving primitives. Splits preserve each input's
            # rank independently; they do not make train and test equivalent.
            for i, ctx, method, _ in self.edges:
                canonical = self.aliases.get(method, method)
                if canonical.endswith("train_test_split"):
                    for (call, retidx), retvar in self.returns.items():
                        src = self.actual.get((i, retidx // 2 + 1))
                        if call == i and src:
                            for mapping in (self.ranks, self.kinds):
                                old = len(mapping[retvar, ctx]); mapping[retvar, ctx].update(mapping[src, ctx])
                                changed |= old != len(mapping[retvar, ctx])
            if not changed:
                break
        self.flows = rows(self.fact_dir, "FlowFrom.csv")
        self.extended_flows = {(a, ac, b, bc) for a, ac, b, bc, _ in rows(self.fact_dir, "FlowFromExtended.csv")}
        self.sinks = {(r[1], r[4]) for name in ("TrainingDataWithModel.csv", "ValOrTestDataWithModel.csv") for r in rows(self.fact_dir, name)}
        self.points_to = defaultdict(set)
        for var, ctx, value, heapctx in rows(self.fact_dir, "VarPointsTo.csv"):
            self.points_to[var, ctx].add((value, heapctx))
        self.invoke_paths = {tuple(r) for r in rows(self.fact_dir, "InvokePath.csv")}

    def canonical_method(self, invo, ctx, method):
        canonical = self.aliases.get(method, method)
        receiver = self.actual.get((invo, 0))
        kinds = self.kinds.get((receiver, ctx), set()) | self.objects.get((receiver, ctx), set())
        if canonical.startswith("Unknown.") and len(kinds) == 1:
            canonical = next(iter(kinds)) + "." + canonical.split(".")[-1]
        return canonical

    def fitted_state(self, invo, ctx, receiver):
        objects = self.points_to.get((receiver, ctx), set())
        fits = []
        for fi, fc, method, _ in self.edges:
            canonical = self.canonical_method(fi, fc, method)
            if canonical.split('.')[0] not in SPECS['stateful_classes'] or canonical.split('.')[-1] not in ('fit', 'fit_transform'):
                continue
            obj = self.actual.get((fi, 0))
            if objects & self.points_to.get((obj, fc), set()) and (invo, ctx, fi, fc) in self.invoke_paths:
                fits.append(fi + ':' + fc)
        # Upstream does not kill all effects on refit. Multiple prior fits remain
        # unsupported, rather than claiming a precise state version from a token.
        return fits[0] if len(set(fits)) == 1 else None

    def constant(self, var, ctx):
        values = self.constants.get((var, ctx), set())
        return next(iter(values))[1] if len(values) == 1 else UNKNOWN

    def rank(self, var, ctx):
        values = self.ranks.get((var, ctx), set())
        return next(iter(values)) if len(values) == 1 else None

    def primitive_arguments(self, invo, ctx, canonical, bound_method):
        """Bind the supported positional prefix; other explicit options abstain."""
        scale = canonical == 'sklearn.preprocessing.scale'
        tail = canonical.split('.')[-1]
        offset = 0 if bound_method else 1
        # quantile has q before axis for both free and bound forms.
        axis_index = offset + (2 if tail == 'quantile' else 1)
        axis_var = self.keywords.get((invo, 'axis'))
        if axis_var is None and not scale:
            axis_var = self.actual.get((invo, axis_index))
        default_axis = 0 if scale or any(x in canonical for x in ('DataFrame', 'Series')) else None
        axis = self.constant(axis_var, ctx) if axis_var else default_axis
        options = {}
        if tail == 'quantile':
            qvar = self.keywords.get((invo, 'q')) or self.actual.get((invo, offset + 1))
            options['q'] = self.constant(qvar, ctx) if qvar else (0.5 if bound_method else UNKNOWN)
        allowed = {'axis', 'q'} if tail == 'quantile' else {'axis'}
        if scale:
            allowed |= {'with_mean', 'with_std', 'copy'}
        # Keep the first implementation conservative about any optional argument
        # not explicitly reviewed (including masks, custom dtype, and mutations).
        for (call, name), var in self.keywords.items():
            if call == invo and name != 'axis':
                options[name] = self.constant(var, ctx)
                if name not in allowed:
                    options['_unsupported_arguments'] = True
        max_position = 1 if scale else axis_index
        if any(call == invo and k > max_position for call, k in self.actual):
            options['_unsupported_arguments'] = True
        return axis, options

    def candidates(self):
        candidates = []
        for invo, ctx, method, _ in sorted(self.edges):
            canonical = self.canonical_method(invo, ctx, method)
            # Resolve method receiver type through actual/formal bindings rather
            # than assuming Unknown.mean is NumPy or pandas.
            receiver = self.actual.get((invo, 0))
            kinds = self.kinds.get((receiver, ctx), set())
            if canonical.startswith("Unknown.") and len(kinds) == 1:
                canonical = next(iter(kinds)) + "." + canonical.split(".")[-1]
            tail = canonical.split(".")[-1]
            owner = canonical.split(".")[-2] if "." in canonical else ""
            scope = self.calls[invo][1]
            outputs = [self.returns.get((invo, 0))]
            if tail in ("fit", "fit_transform"):
                outputs.append(receiver)
            if not any((sink, sinkctx, v, ctx) in self.extended_flows for sink, sinkctx in self.sinks for v in outputs if v):
                continue
            if canonical == "sklearn.preprocessing.scale" or tail in SPECS["reducers"]:
                bound_method = canonical != "sklearn.preprocessing.scale" and not canonical.startswith("numpy.")
                index = 0 if bound_method else 1
                source = self.actual.get((invo, index))
                # Pyright may call ndarray methods Unknown: keep the candidate but
                # cannot prove its semantics without type/rank information.
                axis, parameters = self.primitive_arguments(invo, ctx, canonical, bound_method)
                rank = self.rank(source, ctx)
                effect, reason = primitive_effect(canonical, rank, axis, parameters)
                candidate = self.make_candidate(invo, ctx, method, canonical, scope, source, index,
                                                axis, rank, effect, reason, "return")
                candidate['resolved_parameters'] = {k: 'unresolved' if v is UNKNOWN else v for k,v in parameters.items()}
                candidates.append(candidate)
            elif owner in SPECS["stateful_classes"] and tail in ("fit", "fit_transform", "transform"):
                effect = "apply_state" if tail == "transform" else "fit_state"
                source = self.actual.get((invo, 1))
                candidates.append(self.make_candidate(invo, ctx, method, canonical, scope, source, 1,
                                                      0, self.rank(source, ctx), effect,
                                                      "reviewed stateful API; upstream SSA/pointer propagation retained", "state"))
        return candidates

    def make_candidate(self, invo, ctx, method, canonical, scope, source, index, axis, rank, effect, reason, target):
        line = self.lines[invo]
        node = self.ast_calls.get(line)
        function = self.functions.get(scope)
        segment = ast.get_source_segment(self.ir, function or node) if (function or node) else ""
        ret = self.returns.get((invo, 0))
        dependencies = []
        if scope:
            formal_return = self.formal_returns.get((scope, 0))
            for (m, k), param in self.formals.items():
                if m == scope and any(to == formal_return and tc == ctx and src == param and sc == ctx for to, tc, src, sc, _ in self.flows):
                    dependencies.append({"parameter": k, "target": "function_return"})
        identity = {"source_sha256": self.source_sha, "ir_sha256": digest(self.ir), "invocation": invo,
                    "context": ctx, "primitive_spec_sha256": digest(SPECS)}
        receiver = self.actual.get((invo, 0))
        state_version = invo + ":" + ctx if effect == 'fit_state' else self.fitted_state(invo, ctx, receiver) if effect == 'apply_state' else None
        if effect == 'apply_state' and state_version is None:
            effect, reason = 'unknown', 'no unique preceding fitted object state; refits/ambiguous aliases unsupported'
        return {"candidate_id": digest(identity), **identity, "function_id": scope or "<module>",
                "method": method, "canonical_method": canonical, "code": segment, "ir_line": line,
                "input_variable": source, "input_index": index, "return_variable": ret,
                "receiver": receiver, "state_version": state_version,
                "resolved_axis": "unresolved" if axis is UNKNOWN else axis, "input_rank": rank,
                "resolved_parameters": {},
                "sample_axis": 0, "function_parameter_dependencies": dependencies,
                "deterministic_effect": effect, "proof_reason": reason,
                "evidence": {"line": line, "primitive": canonical, "input": source, "axis": "unresolved" if axis is UNKNOWN else axis}}

def proposed_summary(candidate):
    """Deterministic summary, also useful to build adversarial interface tests."""
    return {"candidate_id": candidate["candidate_id"], "source_sha256": candidate["source_sha256"],
            "ir_sha256": candidate["ir_sha256"], "invocation": candidate["invocation"], "context": candidate["context"],
            "primitive_spec_sha256": candidate["primitive_spec_sha256"],
            "effects": [{"kind": candidate["deterministic_effect"], "input_index": candidate["input_index"],
                         "output_index": 0, "evidence_line": candidate["ir_line"],
                         "primitive": candidate["canonical_method"], "receiver": candidate["receiver"],
                         "state_version": candidate["state_version"]}],
            "unresolved": [candidate["proof_reason"]] if candidate["deterministic_effect"] == "unknown" else []}

def verify(candidate, summary, semantic=True):
    """N0 validates structure/references; N1 additionally checks rule derivability."""
    import jsonschema
    schema = json.loads((ROOT / "specs/summary.schema.json").read_text())
    try:
        jsonschema.validate(summary, schema)
        for key in ("candidate_id", "source_sha256", "ir_sha256", "invocation", "context", "primitive_spec_sha256"):
            if summary[key] != candidate[key]:
                raise ValueError("mismatched " + key)
        for e in summary["effects"]:
            if e["input_index"] != candidate["input_index"] or e["output_index"] != 0:
                raise ValueError("nonexistent parameter/return reference")
            if e["evidence_line"] != candidate["ir_line"] or e["primitive"] != candidate["canonical_method"]:
                raise ValueError("code evidence does not match candidate")
            if e["receiver"] != candidate["receiver"] or e["state_version"] != candidate["state_version"]:
                raise ValueError("object/state reference mismatch")
        if semantic:
            kinds = {e["kind"] for e in summary["effects"]}
            if kinds != {candidate["deterministic_effect"]}:
                raise ValueError("effect lacks deterministic proof: " + candidate["proof_reason"])
        return {"accepted": True, "semantic_checked": semantic, "reason": "verified within declared primitive subset" if semantic else "structure and references only"}
    except (ValueError, KeyError, jsonschema.ValidationError) as e:
        return {"accepted": False, "semantic_checked": semantic, "reason": str(e).splitlines()[0]}

