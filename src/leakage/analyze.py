import json
import subprocess
import time
from pathlib import Path
from .common import ROOT, digest, write_json, implementation_digest
from .effects import Frontend, proposed_summary, verify
from .symbolic import solve
from .projection import train_affecting

def analyze(baseline_dir, out, method="S1", summaries=None, timeout=720):
    start = time.monotonic()
    baseline_dir, out = Path(baseline_dir), Path(out)
    baseline = json.loads((baseline_dir / "result.json").read_text())
    result = {k: baseline[k] for k in ("sample_id", "source_sha256", "status", "location_available")}
    result.update(method=method, diagnostics=[], errors=[], checks=[], summary_batch_sha256=None,
                  unknown_reasons=[], raw_preprocessing_rows=[])
    config = {"method": method, "frontend_version": 1, "timeout": timeout,
              "spec_sha256": digest((ROOT / "specs/primitives.json").read_bytes()),
              "implementation_sha256": implementation_digest()}
    result["config_sha256"] = digest(config)
    if out.exists():
        raise FileExistsError("Refusing to overwrite run: " + str(out))
    out.mkdir(parents=True)
    try:
        if baseline["status"] not in ("leak", "no_finding"):
            result["errors"] = ["Baseline frontend unavailable"] + baseline.get("errors", [])
            return result
        front = Frontend(baseline_dir)
        candidates = front.candidates()
        write_json(out / "candidates.json", candidates)
        if method in ("N0", "N1"):
            if summaries is None:
                raise ValueError("No saved model summary batch; no model experiment performed")
            batch = json.loads(Path(summaries).read_text())
            if batch.get("origin") != "live_api":
                raise ValueError("Offline fixtures cannot be used as experiment results")
            if batch.get("source_sha256") != front.source_sha:
                raise ValueError("Summary batch does not match source")
            result["summary_batch_sha256"] = digest(Path(summaries).read_bytes())
            responses = batch["summaries"]
        elif method != "S1":
            raise ValueError("Unsupported mode")
        effects = []
        for candidate in candidates:
            cid = candidate["candidate_id"]
            summary = proposed_summary(candidate) if method == "S1" else responses.get(cid)
            check = verify(candidate, summary, semantic=method != "N0") if summary is not None else {"accepted": False, "reason": "missing/failed model response"}
            result["checks"].append({"candidate_id": cid, **check})
            if not check["accepted"]:
                # Rejected model responses fall back to the same deterministic
                # knowledge as S1. Unproved effects retain original upstream taint.
                summary = proposed_summary(candidate)
                result["checks"][-1]["fallback"] = "S1 deterministic effects; otherwise original baseline"
            for e in summary["effects"]:
                if e["kind"] == "unknown":
                    result["unknown_reasons"].append({"candidate_id": cid, "reason": candidate["proof_reason"]})
                else:
                    effects.append([candidate["invocation"], candidate["context"], e["kind"], e["input_index"], e["output_index"]])
        raw = solve(baseline_dir, out / "solver", effects, timeout)
        result["raw_preprocessing_rows"] = raw
        result["conservative_fallback_status"] = "leak" if raw else "no_finding"
        result["status"] = "unknown" if result["unknown_reasons"] else "leak" if raw else "no_finding"
        # Do not call the original OR(train,test) rule the narrower task definition.
        # Keep both raw output and a scope-specific train-affecting projection.
        projected = train_affecting(out / "solver/facts")
        result["train_affecting_projection"] = projected
        result["scope_status"] = "unknown" if result["unknown_reasons"] else "leak" if projected else "no_finding"
        result["scope_projection_limit"] = "train dependence and evaluation overlap joined with the exact reduction contexts; no safe-program claim"
        if method in ('N0','N1') and candidates and not any(responses.get(c['candidate_id']) is not None for c in candidates):
            result['fallback_scope_status'] = result['scope_status']
            result['status'] = result['scope_status'] = 'error'
            result['errors'].append('No parseable model responses; symbolic fallback retained but neural run failed')
    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["errors"].append("Derived Datalog timeout")
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))
    finally:
        result["elapsed_seconds"] = time.monotonic() - start
        result["frontend_elapsed_seconds"] = baseline["elapsed_seconds"]
        write_json(out / "result.json", result)
    return result

