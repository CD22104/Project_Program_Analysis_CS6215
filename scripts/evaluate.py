import argparse
import csv
import json
from leakage.common import ROOT, write_json
from leakage.evaluate import compare

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--predictions',required=True)
    p.add_argument('--labels',default='data/annotations/controlled.json')
    p.add_argument('--out',required=True)
    p.add_argument('--provisional',action='store_true')
    args=p.parse_args()
    predictions=json.loads((ROOT/args.predictions).read_text())
    records=json.loads((ROOT/args.labels).read_text())
    ids={r['sample_id'] for r in predictions}
    relevant=[r for r in records if r['sample_id'] in ids]
    pending=any(r['review_status']!='student_reviewed' for r in relevant)
    if pending and not args.provisional:
        raise SystemExit('Labels have not been reviewed; use --provisional for explicitly provisional metrics.')
    result=compare(predictions,{r['sample_id']:r['label'] for r in relevant})
    result['label_status']='provisional; pending student review' if pending else 'student_reviewed'
    result['predictions_file']=args.predictions
    result['labels_file']=args.labels
    out=ROOT/args.out
    out.mkdir(parents=True,exist_ok=True)
    write_json(out/'metrics.json',result)
    table=[{'method':method,**r} for method,r in result['primary_scope_projection'].items()]
    with (out/'metrics.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    print(json.dumps(result['primary_scope_projection'],indent=2))

if __name__=='__main__':main()
