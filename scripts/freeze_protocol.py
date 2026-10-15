"""Create an immutable evaluation plan after model setup and development checks."""
import argparse,json,random
from leakage.common import ROOT,digest,write_json,implementation_digest
from leakage.model import config

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',default='configs/frozen-protocol.json')
    args=p.parse_args()
    output=ROOT/args.out
    if output.exists():raise SystemExit('Freeze exists; preserve it and create an explicitly versioned revision.')
    connection=json.loads((ROOT/'runs/environment/model-connectivity.json').read_text())
    cfg=config()
    if not connection.get('connected') or cfg['SOCLAAS_MODEL']=='default':
        raise SystemExit('A reachable service and fixed model ID are required before formal freeze.')
    manifests={n:json.loads((ROOT/'data/manifests'/n).read_text()) for n in ('controlled.json','real.json','variants.json')}
    families=sorted({r['family'] for r in manifests['controlled.json'] if r['partition']=='test_pending_freeze'})
    repeats=random.Random(6215).sample(families,min(12,len(families)))
    repeat_subjects=[sorted(r['sample_id'] for r in manifests['controlled.json'] if r['family']==family)[0]
                     for family in repeats]
    frozen={name:[{**r,'partition':'test' if r['partition']=='test_pending_freeze' else r['partition']} for r in records]
            for name,records in manifests.items()}
    protocol={'implementation_sha256':implementation_digest(),'model':cfg['SOCLAAS_MODEL'],
              'prompt_sha256':digest((ROOT/'prompts/effects-v1.txt').read_bytes()),
              'baseline_timeout_seconds':720,'repeat_families':repeats,
              'repeat_subjects':repeat_subjects,'replicates':[0,1,2],
              'student_label_review':'pending','student_method_review':'pending',
              'cohort_hashes':{n:digest(r) for n,r in manifests.items()},
              'frozen_cohort_hashes':{n:digest(r) for n,r in frozen.items()},
              'primary_metric':'program-level train-affecting scope projection',
              'reporting':'controlled, real, and paired variants separate; unreviewed labels provisional'}
    write_json(output,protocol)
    # Write new frozen manifests; never mutate original development manifests.
    for name,records in frozen.items():
        write_json(ROOT/'data/manifests/frozen'/name,records)
    print(output.relative_to(ROOT))

if __name__=='__main__':main()
