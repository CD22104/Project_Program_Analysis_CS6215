"""Reuse saved S0 frontends; no model or label access."""
import argparse
import json
from leakage.common import ROOT, write_json
from leakage.analyze import analyze
from leakage.projection import train_affecting

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline-run', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--methods', nargs='+', default=['S1'], choices=['S1','N0','N1'])
    p.add_argument('--summaries')
    p.add_argument('--sample-id',nargs='+',help='Optional fixed repeat-study subject IDs')
    args = p.parse_args()
    prior = ROOT / args.baseline_run
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((prior / 'manifest.json').read_text())
    if args.sample_id:
        if not set(args.sample_id)<={s['sample_id'] for s in manifest}:
            raise SystemExit('Requested subject is absent from the baseline cohort')
        manifest=[s for s in manifest if s['sample_id'] in set(args.sample_id)]
    write_json(out / 'manifest.json', manifest)
    results = []
    for subject in manifest:
        sid = subject['sample_id']
        base = prior / sid / 'S0'
        b = json.loads((base / 'result.json').read_text())
        if b['status'] in ('leak','no_finding'):
            b['train_affecting_projection'] = train_affecting(base / 'work/input-fact')
            b['scope_status'] = 'leak' if b['train_affecting_projection'] else 'no_finding'
        b['evidence_run'] = str(base.relative_to(ROOT))
        results.append(b)
        for method in args.methods:
            summary = ROOT / args.summaries / (sid + '.json') if args.summaries else None
            r = analyze(base, out / sid / method, method, summary)
            r.update({k: subject.get(k) for k in ('sample_id','family','partition','source_kind','variant','base_sample_id')})
            write_json(out / sid / method / 'result.json', r)
            results.append(r)
            print(sid,method,r['status'],r['errors'],flush=True)
    write_json(out / 'predictions.json', results)

if __name__ == '__main__':
    main()
