"""Rebuild every reported study table from saved evidence; never calls a model."""
import argparse,csv,json,statistics
from collections import Counter
from leakage.common import ROOT,write_json
from leakage.evaluate import compare
from leakage.study import paired_variants,repeated_predictions,model_evidence

COHORTS={'development':('neural-pilot-v1','model-pilot-v1','controlled'),
 'real-development':('neural-real-pilot-v1','model-real-pilot-v1','real-reviewed'),
 'controlled':('formal-controlled-neural-v1','formal-controlled-model-v1','controlled'),
 'real':('formal-real-neural-v1','formal-real-model-v1','real-reviewed'),
 'variants':('formal-variants-neural-v1','formal-variants-model-v1','variants')}
def read(p):return json.loads((ROOT/p).read_text())
def rawrecord(k):
    p=ROOT/'runs/model-cache'/(k+'.json')
    return json.loads(p.read_text()) if p.exists() else read('runs/public-model-records/'+k+'.json')
def batches(folder):return [json.loads(p.read_text()) for p in sorted((ROOT/'runs'/folder).glob('*.json')) if p.name!='generation-manifest.json']
def table(path,rows):
    if not rows:return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def texnum(x):return '--' if x is None else '%.3f'%x

def main():
    p=argparse.ArgumentParser();p.add_argument('--require-formal',action='store_true');args=p.parse_args()
    out=ROOT/'results/study';out.mkdir(parents=True,exist_ok=True)
    allpred={};allbatches=[];results={};metricrows=[];costrows=[];checks=[];timing=[]
    for name,(run,gen,annotation) in COHORTS.items():
        path=ROOT/'runs'/run/'predictions.json'
        if not path.exists():
            if args.require_formal:raise SystemExit('Missing required cohort: '+name)
            continue
        pred=json.loads(path.read_text());allpred[name]=pred
        rows=read('data/annotations/'+annotation+'.json')
        labels={r['sample_id']:r['label'] for r in rows if r.get('label') is not None}
        result=compare(pred,labels)
        result.update(label_status='partial student review; unlabelled subjects excluded from confusion' if annotation=='real-reviewed' else 'provisional constructed labels; student review pending',predictions_file=str(path.relative_to(ROOT)))
        bs=batches(gen);allbatches+=bs
        keys={k for b in bs for k in b['records'].values()}
        result['model']=model_evidence(bs,{k:rawrecord(k) for k in keys},pred)
        for method,r in result['primary_scope_projection'].items():metricrows.append({'cohort':name,'method':method,**r})
        costrows.append({'cohort':name,**result['model']['costs']})
        for method,r in result['model']['verification'].items():checks.append({'cohort':name,'method':method,**r})
        for method in ('S0','S1','N0','N1'):
            rs=[r for r in pred if r['method']==method]
            elapsed=[r['elapsed_seconds'] for r in rs]
            frontend=[r.get('frontend_elapsed_seconds',r['elapsed_seconds']) for r in rs]
            timing.append({'cohort':name,'method':method,'scheduled':len(rs),'replay_stage_seconds_total':sum(elapsed),'replay_stage_seconds_median':statistics.median(elapsed),'frontend_seconds_total':sum(frontend),'shared_generation_seconds':sum(b['generation_elapsed_seconds'] for b in bs) if method in ('N0','N1') else 0,'first_pass_serial_seconds_sum':sum(elapsed)+(sum(frontend) if method!='S0' else 0)+(sum(b['generation_elapsed_seconds'] for b in bs) if method in ('N0','N1') else 0),'note':'S0 elapsed already includes frontend; S1/N0/N1 elapsed is additional stage; generation charged once to shared N0/N1'})
        results[name]=result;write_json(out/(name+'.json'),result)
    studies={}
    if 'variants' in allpred:
        labels={r['sample_id']:r['label'] for f in ('controlled','variants') for r in read('data/annotations/'+f+'.json')}
        studies['paired_variants']=paired_variants(allpred['controlled'],allpred['variants'],labels)
        table(out/'paired-variants.csv',studies['paired_variants'])
    if (ROOT/'runs/repeat-2-neural-v1/predictions.json').exists():
        ids=read('configs/frozen-protocol.json')['repeat_subjects']
        reps=[[r for r in allpred['controlled'] if r['sample_id'] in ids]]
        for rep in (1,2):
            pred=read('runs/repeat-%d-neural-v1/predictions.json'%rep);reps.append(pred)
            bs=batches('repeat-%d-model-v1'%rep);allbatches+=bs
            keys={k for b in bs for k in b['records'].values()}
            evidence=model_evidence(bs,{k:rawrecord(k) for k in keys},pred)
            studies['repeat_%d_model'%rep]=evidence
            costrows.append({'cohort':'repeat-'+str(rep),**evidence['costs']})
        studies['repetition']=repeated_predictions(reps,ids)
        table(out/'repetition.csv',[{'method':m,**v} for m,v in studies['repetition'].items()])
        studies['repeat_subjects_with_candidates']={str(rep):sum(bool(b['records']) for b in batches('formal-controlled-model-v1' if rep==0 else 'repeat-%d-model-v1'%rep) if b['source_sha256'] in {r['source_sha256'] for r in reps[rep]}) for rep in range(3)}
    elif args.require_formal:raise SystemExit('Repeat study not complete')
    # Include the first connectivity inference; avoid double-charging its later cache hit.
    allbatches+=batches('model-connectivity-pilot')
    keys={k for b in allbatches for k in b['records'].values()}
    studies['all_model_usage']=model_evidence(allbatches,{k:rawrecord(k) for k in keys},[]) if allbatches else {}
    studies['monetary_expenditure']=0
    studies['inference_service']='user-authorized free SoCLaaS; no paid fallback'
    write_json(out/'study.json',studies)
    table(out/'metrics.csv',metricrows);table(out/'costs.csv',costrows);table(out/'verification.csv',checks);table(out/'timing.csv',timing)
    lines=[r'\begin{table*}[t]',r'\caption{Actual program-level training-affecting results. Constructed labels remain provisional. Real cohorts report execution coverage; only one development positive has student review. F1 is conditional on successful labelled results.}',r'\label{tab:all}',r'\centering\begin{tabular}{llrrrrrrrrr}',r'\toprule Cohort & Method & TP & FP & FN & TN & Unknown & Error & Timeout & Success & F1\\\midrule']
    for r in metricrows:
        real=r['cohort'].startswith('real')
        nums=['--' if real else str(r[k]) for k in ('TP','FP','FN','TN')]
        lines.append(' & '.join([r['cohort'],r['method']]+nums+[str(r[k]) for k in ('unknown','error','timeout')]+[str(r['success'])+'/'+str(r['scheduled']),'--' if real else texnum(r['conditional_f1'])])+r'\\')
    lines += [r'\bottomrule\end{tabular}',r'\end{table*}'];(ROOT/'report/generated-all.tex').write_text('\n'.join(lines)+'\n')
    lines=[r'\begin{table}[t]',r'\caption{Shared generation and semantic verification. Tokens count new requests only; cached requests are charged at original generation.}',r'\label{tab:cost}',r'\centering\begin{tabular}{lrrr}',r'\toprule Cohort & Candidates & Tokens & N1 rejected\\\midrule']
    for name,r in results.items():
        c=r['model']['costs'];v=r['model']['verification'].get('N1',{})
        lines.append('%s & %d & %d & %d/%d'%(name,c.get('candidate_references',0),c.get('reported_total_tokens',0),v.get('rejected',0),v.get('total',0))+r'\\')
    lines += [r'\bottomrule\end{tabular}',r'\end{table}'];(ROOT/'report/generated-cost.tex').write_text('\n'.join(lines)+'\n')
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    selected=[n for n in ('development','controlled','variants') if n in results]
    fig,axes=plt.subplots(1,len(selected),figsize=(3.2*len(selected),2.7),squeeze=False)
    colors={'TP':'#1b9e77','TN':'#66a61e','FP':'#d95f02','FN':'#7570b3','unknown':'#999999','error':'#444444','timeout':'#e6ab02'}
    for ax,n in zip(axes[0],selected):
        ms=results[n]['primary_scope_projection'];methods=list(ms);left=[0]*len(methods)
        for k,c in colors.items():
            values=[ms[m][k] for m in methods];ax.barh(methods,values,left=left,color=c,label=k);left=[a+b for a,b in zip(left,values)]
        ax.set_title(n);ax.set_xlabel('Programs (provisional labels)');ax.spines[['top','right']].set_visible(False)
    handles,labels=axes[0][0].get_legend_handles_labels();fig.legend(handles,labels,ncol=7,loc='upper center',fontsize=8)
    fig.tight_layout(rect=(0,0,1,.88));fig.savefig(out/'counts.pdf',bbox_inches='tight');plt.close(fig)
    write_json(ROOT/'results/all-rebuild-provenance.json',{'cohorts':{n:r['predictions_file'] for n,r in results.items()},'model_requests_made':0,'model_records':'private originals or exported response-only evidence','formal_complete':all(n in results for n in ('controlled','real','variants')) and 'repetition' in studies})
    print('Rebuilt',list(results),'from saved predictions and responses only.')

if __name__=='__main__':main()
