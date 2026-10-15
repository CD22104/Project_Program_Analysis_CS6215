import argparse
import json
import time
from leakage.common import ROOT, write_json, implementation_digest
from leakage.effects import Frontend
from leakage.model import config, Budget, generate

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline-run', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--stage', choices=['pilot','formal'], default='pilot')
    p.add_argument('--repeat', type=int, default=0)
    p.add_argument('--sample-id', nargs='+', help='Optional fixed repeat-study subject IDs')
    args = p.parse_args()
    cfg = config()
    if args.stage == 'formal':
        protocol = json.loads((ROOT/'configs/frozen-protocol.json').read_text())
        if protocol['implementation_sha256'] != implementation_digest() or protocol['model'] != cfg['SOCLAAS_MODEL']:
            raise SystemExit('Frozen implementation/model mismatch')
    prior, out = ROOT / args.baseline_run, ROOT / args.out
    out.mkdir(parents=True, exist_ok=False)
    budget = Budget(ROOT / 'runs/model-budget' / (args.stage + '.jsonl'), 200000 if args.stage == 'pilot' else 1000000)
    subjects = json.loads((prior / 'manifest.json').read_text())
    if args.sample_id:
        if not set(args.sample_id) <= {s['sample_id'] for s in subjects}:
            raise SystemExit('Requested subject is absent from the baseline cohort')
        subjects=[s for s in subjects if s['sample_id'] in set(args.sample_id)]
    write_json(out/'generation-manifest.json',{'subjects':[s['sample_id'] for s in subjects],
               'stage':args.stage,'replicate':args.repeat,'baseline_run':args.baseline_run})
    for subject in subjects:
        sid = subject['sample_id']
        base = prior / sid / 'S0'
        b = json.loads((base / 'result.json').read_text())
        if b['status'] not in ('leak','no_finding'):
            continue
        front = Frontend(base)
        batch = {'origin': 'live_api', 'source_sha256': front.source_sha, 'model': cfg['SOCLAAS_MODEL'],
                 'summaries': {}, 'records': {}, 'cache_hits':{}, 'replicate': args.repeat}
        started=time.monotonic()
        for candidate in front.candidates():
            record = generate(candidate, cfg, ROOT / 'runs/model-cache', budget, args.repeat)
            cid = candidate['candidate_id']
            batch['summaries'][cid] = record['summary']
            batch['records'][cid] = record['cache_key']
            batch['cache_hits'][cid] = record['cache_hit']
        batch['generation_elapsed_seconds']=time.monotonic()-started
        write_json(out / (sid + '.json'), batch)
        print(sid, len(batch['summaries']), 'candidates', flush=True)

if __name__ == '__main__':
    main()
