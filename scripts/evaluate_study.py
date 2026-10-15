"""Summarize saved study outputs only; no model calls or program execution."""
import argparse,json
from leakage.common import ROOT,write_json
from leakage.study import paired_variants,repeated_predictions,model_evidence

def read(path):return json.loads((ROOT/path).read_text())

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--predictions',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--variants')
    p.add_argument('--labels',nargs='*',default=[])
    p.add_argument('--provisional',action='store_true')
    p.add_argument('--repeat-predictions',nargs=3)
    p.add_argument('--protocol',default='configs/frozen-protocol.json')
    p.add_argument('--summaries',nargs='*',default=[])
    args=p.parse_args()
    predictions=read(args.predictions)
    labels={};pending=False
    for path in args.labels:
        for row in read(path):
            labels[row['sample_id']]=row['label']
            pending |= row['review_status']!='student_reviewed'
    if pending and not args.provisional:raise SystemExit('Unreviewed labels require --provisional')
    output={'label_status':'provisional' if pending else 'not supplied' if not labels else 'student_reviewed'}
    if args.variants:output['paired_variants']=paired_variants(predictions,read(args.variants),labels)
    if args.repeat_predictions:
        output['repetition']=repeated_predictions([read(f) for f in args.repeat_predictions],read(args.protocol)['repeat_subjects'])
    if args.summaries:
        batches=[]
        for folder in args.summaries:
            batches.extend(json.loads(f.read_text()) for f in (ROOT/folder).glob('*.json') if f.name!='generation-manifest.json')
        keys={key for b in batches for key in b['records'].values()}
        records={key:read('runs/model-cache/'+key+'.json') for key in keys}
        output['model_evidence']=model_evidence(batches,records,predictions)
    write_json(ROOT/args.out,output)
    print('Rebuilt study summary from saved evidence only.')

if __name__=='__main__':main()
