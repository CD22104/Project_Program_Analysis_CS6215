"""Run the frozen four-method study. No evaluator or annotation imports."""
import argparse,json,subprocess,sys
from leakage.common import ROOT,implementation_digest

def run(script,*args):
    subprocess.run([sys.executable,str(ROOT/'scripts'/script),*args],cwd=ROOT,check=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--prefix',default='formal');p.add_argument('--cohort',choices=['controlled','real','variants','repeats','all'],default='all');args=p.parse_args()
    protocol=json.loads((ROOT/'configs/frozen-protocol.json').read_text())
    if protocol['implementation_sha256']!=implementation_digest():raise SystemExit('Implementation changed after freeze')
    for name in ('controlled','real','variants'):
        if args.cohort not in (name,'all'):continue
        base='runs/'+args.prefix+'-'+name+'-v1';model='runs/'+args.prefix+'-'+name+'-model-v1';neural='runs/'+args.prefix+'-'+name+'-neural-v1'
        run('run_experiment.py','--manifest','data/manifests/frozen/'+name+'.json','--partition','test','--out',base,'--methods','S0')
        run('generate_summaries.py','--baseline-run',base,'--out',model,'--stage','formal')
        run('replay_effects.py','--baseline-run',base,'--out',neural,'--methods','S1','N0','N1','--summaries',model)
    if args.cohort in ('repeats','all'):
        for rep in (1,2):
            base='runs/'+args.prefix+'-controlled-v1';model='runs/repeat-%d-model-v1'%rep;neural='runs/repeat-%d-neural-v1'%rep
            ids=protocol['repeat_subjects']
            run('generate_summaries.py','--baseline-run',base,'--out',model,'--stage','formal','--repeat',str(rep),'--sample-id',*ids)
            run('replay_effects.py','--baseline-run',base,'--out',neural,'--methods','S1','N0','N1','--summaries',model,'--sample-id',*ids)

if __name__=='__main__':main()
