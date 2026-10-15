"""Runs selected manifests without ever opening annotations."""
import argparse
import json
from pathlib import Path
from leakage.baseline import run
from leakage.analyze import analyze
from leakage.common import ROOT, write_json,digest,implementation_digest

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", default="data/manifests/controlled.json")
    p.add_argument("--partition", choices=["dev", "test"], default="dev")
    p.add_argument("--out", required=True)
    p.add_argument("--methods", nargs="+", choices=["S0", "S1", "N0", "N1"], default=["S0", "S1"])
    p.add_argument("--summaries", type=Path)
    p.add_argument("--timeout", type=int, default=720)
    args = p.parse_args()
    manifest = json.loads((ROOT / args.manifest).read_text())
    if args.partition=='test':
        protocol=json.loads((ROOT/'configs/frozen-protocol.json').read_text())
        if protocol['implementation_sha256']!=implementation_digest():
            raise SystemExit('Implementation/dependency files changed after freeze; preserve results and version the protocol.')
        if protocol['frozen_cohort_hashes'].get(Path(args.manifest).name)!=digest(manifest):
            raise SystemExit('Test manifest differs from the frozen cohort')
    selected = [r for r in manifest if r["partition"] == args.partition]
    if not selected:
        raise SystemExit("No eligible subjects (test partition requires protocol freeze).")
    for subject in selected:
        if digest((ROOT/subject['source_path']).read_bytes())!=subject['source_sha256']:
            raise SystemExit('Source differs from manifest: '+subject['sample_id'])
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=False)
    all_results = []
    write_json(out / "manifest.json", selected)
    for subject in selected:
        sid = subject["sample_id"]
        source = ROOT / subject["source_path"]
        base = out / sid / "S0"
        b = run(source, base, args.timeout)
        for mode in args.methods:
            batch = args.summaries / (sid + ".json") if args.summaries else None
            r = b if mode == "S0" else analyze(base, out / sid / mode, mode, batch, args.timeout)
            for key in ("family", "partition", "source_kind", "variant", "base_sample_id"):
                r[key] = subject.get(key)
            # Input is always named input.py in work; use manifest ID for evaluation.
            r["sample_id"] = sid
            write_json(out / sid / mode / "result.json", r)
            all_results.append(r)
            print(json.dumps({"sample_id": sid, "method": mode, "status": r["status"], "errors": r["errors"]}), flush=True)
    write_json(out / "predictions.json", all_results)

if __name__ == "__main__":
    main()
