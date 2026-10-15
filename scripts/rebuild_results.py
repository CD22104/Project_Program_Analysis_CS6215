"""Rebuild tables and a standalone PDF figure from saved predictions only."""
import argparse,json,csv
from collections import Counter
from leakage.common import ROOT,write_json
from leakage.evaluate import compare

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--controlled-run',default='runs/neural-pilot-v1')
    p.add_argument('--real-run',default='runs/neural-real-pilot-v1')
    args=p.parse_args()
    predictions=json.loads((ROOT/args.controlled_run/'predictions.json').read_text())
    labels=json.loads((ROOT/'data/annotations/controlled.json').read_text())
    result=compare(predictions,{r['sample_id']:r['label'] for r in labels})
    result.update(label_status='provisional; all labels pending student review',partition='development',source_run=args.controlled_run)
    out=ROOT/'results/pilot';out.mkdir(parents=True,exist_ok=True)
    write_json(out/'metrics.json',result)
    metrics=result['primary_scope_projection']
    with (out/'metrics.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['method']+list(next(iter(metrics.values()))));w.writeheader()
        w.writerows({'method':m,**r} for m,r in metrics.items())
    real_path=ROOT/args.real_run/'predictions.json'
    real={}
    if real_path.exists():
        records=json.loads(real_path.read_text())
        real={m:dict(Counter(r.get('scope_status',r['status']) for r in records if r['method']==m)) for m in sorted({r['method'] for r in records})}
        write_json(ROOT/'results/real-development-status.json',{'run':args.real_run,'counts':real,'gold_label_metrics':'not reported; event labels pending review'})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(5.6,2.7))
    colors={'TP':'#1b9e77','TN':'#66a61e','FP':'#d95f02','FN':'#7570b3','unknown':'#999999','error':'#444444','timeout':'#e6ab02'}
    methods=list(metrics)
    totals=[0]*len(methods)
    for key,color in colors.items():
        values=[metrics[m][key] for m in methods]
        ax.barh(methods,values,left=totals,label=key,color=color)
        totals=[a+b for a,b in zip(totals,values)]
    ax.set_xlabel('Programs (development only; labels pending review)')
    ax.set_xlim(0,max(totals)+.5)
    ax.legend(ncol=4,fontsize=8,loc='upper center',bbox_to_anchor=(.5,1.3))
    ax.spines[['top','right']].set_visible(False)
    fig.tight_layout();fig.savefig(out/'development-counts.pdf',bbox_inches='tight');plt.close(fig)
    generated=ROOT/'report/generated.tex'
    lines=[r'\begin{table}[t]',r'\caption{Actual controlled development pilot. Labels are provisional; neural modes replay the same actual summaries.}',
           r'\label{tab:pilot}',r'\centering\begin{tabular}{lrrrrrr}',r'\toprule Method & TP & FP & FN & TN & Success & F1\\\midrule']
    for method,r in metrics.items():
        f1='--' if r['conditional_f1'] is None else '%.2f'%r['conditional_f1']
        lines.append(f"{method} & {r['TP']} & {r['FP']} & {r['FN']} & {r['TN']} & {r['success']}/{r['scheduled']} & {f1} " + r'\\')
    lines += [r'\bottomrule\end{tabular}',r'\end{table}']
    generated.write_text('\n'.join(lines)+'\n')
    write_json(ROOT/'results/rebuild-provenance.json',{'controlled_predictions':args.controlled_run+'/predictions.json',
               'real_predictions':args.real_run+'/predictions.json','model_requests_made':0})
    print('Rebuilt provisional metrics, report table, and PDF plot from saved outputs.')

if __name__=='__main__':main()
