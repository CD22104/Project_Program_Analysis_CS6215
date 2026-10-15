"""Rebuild supplementary tables/text from saved frozen outputs and review evidence."""
import csv,json
from collections import Counter
from leakage.common import ROOT,write_json
from leakage.evaluate import compare

def read(p):return json.loads((ROOT/p).read_text())
def main():
    study=read('results/study/study.json');pairs=study['paired_variants']
    text=[r'\begin{table}[t]',r'\caption{Paired variants in the original scheduled cohort. Flip denominators use successful pairs; stable wrong counts preserve consistently incorrect predictions.}',r'\label{tab:variants}',r'\centering\small\begin{tabular}{llrrr}',r'\toprule Method & Variant & Flips/pairs & Status changes & Stable wrong\\\midrule']
    for r in pairs:
        text.append('%s & %s & %d/%d & %d/%d & %d'%(r['method'],r['variant'],r.get('binary_flips',0),r.get('successful_pairs',0),r.get('status_changes',0),r['scheduled_pairs'],r.get('stable_wrong',0))+r'\\')
    text += [r'\bottomrule\end{tabular}',r'\end{table}']
    ids=read('configs/frozen-protocol.json')['repeat_subjects']
    counts=Counter(subjects=len(ids))
    for sid in ids:
        bs=[read('runs/'+f+'/'+sid+'.json') for f in ('formal-controlled-model-v1','repeat-1-model-v1','repeat-2-model-v1')]
        counts['subjects_with_candidates']+=int(bool(bs[0]['summaries']))
        for cid in bs[0]['summaries']:
            ss=[b['summaries'][cid] for b in bs];counts['candidate_triples']+=1
            counts['full_summary_agreement']+=int(len({json.dumps(s,sort_keys=True) for s in ss})==1)
            counts['kind_set_agreement']+=int(len({tuple(sorted(e['kind'] for e in s['effects'])) if s else None for s in ss})==1)
    write_json(ROOT/'results/study/repeated-summary-audit.json',dict(counts))
    rep=study['repetition']
    text.append('Within each method, predictions are unchanged across the three generations for %d/%d scheduled subjects. Of these, %d have candidates, producing %d candidate triples; all %d full parsed summaries agree. This observation does not establish absolute determinism at temperature zero. S0/S1 do not regenerate model answers; their repeat columns describe a fixed symbolic control.'%(rep['N1']['binary_agreement'],rep['N1']['subjects'],counts['subjects_with_candidates'],counts['candidate_triples'],counts['full_summary_agreement']))
    c=study['all_model_usage']['costs']
    text.append('Across development, scheduled formal cohorts and repeats, %d unique actual request records report %s tokens (%s input and %s output). There are %d request attempts, %d candidate cache-hit references, and %d budget-exhausted records. The response evidence reports %d attempts without token usage; zero is claimed only where this counter is zero. Total monetary expenditure is zero under the authorized free service.'%(c['unique_records'],format(c['reported_total_tokens'],','),format(c['reported_prompt_tokens'],','),format(c['reported_completion_tokens'],','),c['new_request_attempts'],c['cache_hits'],c.get('budget_exhausted_records',0),c.get('new_attempts_without_reported_usage',0)))
    (ROOT/'report/robustness.tex').write_text('\n'.join(text)+'\n')
    labels={r['sample_id']:r['label'] for r in read('data/annotations/controlled.json')}
    pred=read('runs/formal-controlled-neural-v1/predictions.json');rows=[]
    for family in sorted({r['family'] for r in pred}):
        metrics=compare([r for r in pred if r['family']==family],labels)['primary_scope_projection']
        rows.extend({'family':family,'method':m,**v} for m,v in metrics.items())
    with (ROOT/'results/study/by-family.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    audit=read('results/study/summary-audit.json')
    counts=Counter((r['cohort'],str(r['rule_effect']),','.join(r['proposed_effects']),r['N1_accepted']) for r in audit)
    write_json(ROOT/'results/study/summary-audit-counts.json',[{'cohort':cohort,'rule_effect':rule,'proposed_effects':prop,'N1_accepted':a,'count':n} for (cohort,rule,prop,a),n in sorted(counts.items())])
    print('Rebuilt robustness, repeat-summary, cost text, family breakdown and saved rule audit counts.')
if __name__=='__main__':main()
