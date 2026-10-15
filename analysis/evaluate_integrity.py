"""Post-hoc integrity sensitivity, introduced after detecting source overlap.
Does not alter frozen predictions, cohorts, prompts, methods, or labels.
"""
import json,csv
from collections import defaultdict
from leakage.common import ROOT,write_json,digest
from leakage.evaluate import compare
from leakage.study import paired_variants,repeated_predictions

def read(path):return json.loads((ROOT/path).read_text())
def main():
    m=read('data/manifests/frozen/controlled.json')
    dev={r['source_sha256'] for r in m if r['partition']=='dev'}
    collisions=[r for r in m if r['partition']=='test' and r['source_sha256'] in dev]
    excluded={r['family'] for r in collisions}
    included={r['sample_id'] for r in m if r['partition']=='test' and r['family'] not in excluded}
    record={'analysis_status':'post hoc integrity sensitivity, not preregistered; original frozen cohort retained',
            'exclusion_rule':'Exclude an entire test family if any of its source hashes equals a development source hash. No predictions or labels used in selection.',
            'excluded_families':sorted(excluded),'collision_subjects':[r['sample_id'] for r in collisions],
            'included_subjects':sorted(included),'code_sha256':digest(__file__ and open(__file__,'rb').read()),
            'independence_limit':'Removes exact cross-partition source overlap only; does not establish template or semantic independence.'}
    labels={r['sample_id']:r['label'] for file in ('controlled','variants') for r in read('data/annotations/'+file+'.json')}
    pred=[r for r in read('runs/formal-controlled-neural-v1/predictions.json') if r['sample_id'] in included]
    record['controlled']=compare(pred,labels)
    vp=ROOT/'runs/formal-variants-neural-v1/predictions.json'
    if vp.exists():
        variants=[r for r in json.loads(vp.read_text()) if r['base_sample_id'] in included]
        record['variants']=compare(variants,labels)
        record['paired_variants']=paired_variants(pred,variants,labels)
    if (ROOT/'runs/repeat-2-neural-v1/predictions.json').exists():
        ids=set(read('configs/frozen-protocol.json')['repeat_subjects'])&included
        reps=[[r for r in pred if r['sample_id'] in ids]]
        reps += [[r for r in read('runs/repeat-%d-neural-v1/predictions.json'%rep) if r['sample_id'] in ids] for rep in (1,2)]
        record['repeat_subjects']=sorted(ids);record['repetition']=repeated_predictions(reps,ids)
    write_json(ROOT/'results/study/integrity-sensitivity.json',record)
    rows=[{'cohort':cohort,'method':method,**metric} for cohort in ('controlled','variants') if cohort in record for method,metric in record[cohort]['primary_scope_projection'].items()]
    with (ROOT/'results/study/integrity-sensitivity.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    tex=[r'\begin{table}[t]',r'\caption{Post-hoc integrity sensitivity: exclude all of F22/F23 after discovering exact development--test source overlap. Original scheduled results remain in Table~\ref{tab:all}. Labels are provisional.}',r'\label{tab:integrity}',r'\centering\begin{tabular}{llrrrrr}',r'\toprule Cohort & Method & TP & FP & FN & TN & F1\\\midrule']
    for r in rows:
        tex.append('%s & %s & %d & %d & %d & %d & %.3f'%(r['cohort'],r['method'],r['TP'],r['FP'],r['FN'],r['TN'],r['conditional_f1'])+r'\\')
    tex += [r'\bottomrule\end{tabular}',r'\end{table}'];(ROOT/'report/generated-integrity.tex').write_text('\n'.join(tex)+'\n')
    generated=ROOT/'report/generated-all.tex'
    if generated.exists():
        generated.write_text(generated.read_text().replace('only one development positive has student review','five positives (two development, three reserved) have student review'))
    print('Post-hoc integrity sensitivity:',len(included),'programs; excluded families',sorted(excluded))
if __name__=='__main__':main()
