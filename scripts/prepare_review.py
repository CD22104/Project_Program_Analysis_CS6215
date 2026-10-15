"""Evaluator-only development review packet. Never imported by model code.

No automatic label revisions. Held-out source and labels are not inspected here.
The output stays in the private annotation directory outside the public artifact.
"""
import argparse
import json
import re
from pathlib import Path
from leakage.common import ROOT, digest, write_json

NOTES = {
    'real_c0650c9464b4': {
        'scope_proposal': 'numeric tabular; full notebook review pending',
        'events': [{'lines': [198,205,218,237], 'proposal': 'negative for this scaler event',
                    'reason': 'Split precedes MinMaxScaler fitting on df_train; df_test uses the same state.'}],
        'program_label_proposal': None,
    },
    'real_4df8bde21c84': {
        'scope_proposal': 'categorical vocabulary learning is outside the initial numeric primitive subset',
        'events': [{'lines': [16,17,18,19,24,29,30], 'proposal': 'review vocabulary/state scope',
                    'reason': 'Feature LabelEncoder mappings are learned before the split. Decide whether global category discovery is included; do not infer safety from no finding.'}],
        'program_label_proposal': None,
    },
    'real_766491df25c7': {
        'scope_proposal': 'text/vectorizer extension; outside the initial numeric table core',
        'events': [{'lines': [319,330,331,334,336], 'proposal': 'negative for this fitted vocabulary event',
                    'reason': 'TFIDF state is fitted on X_train and reused on X_test.'}],
        'program_label_proposal': None,
    },
    'real_38101a98cc8f': {
        'scope_proposal': 'numeric table; proposed in-scope positive',
        'events': [{'lines': [33,34,35,70,78,103,111,278,284], 'proposal': 'positive',
                    'reason': 'Full-data column means fill missing features before the split; filled training features reach model fitting. Separate test-only scaler fitting at line 278 does not explain this primary-task positive.'}],
        'program_label_proposal': True,
    },
    'real_926b37074ebc': {
        'scope_proposal': 'tabular feature selection; author-negative disagreement pending review',
        'events': [{'lines': [35,43,46,48,53,55,59,61], 'proposal': 'positive for feature selection; scaler itself uses training only',
                    'reason': 'Feature columns are selected using full-data correlation with Win before train_test_split. Evaluation rows and targets influence the representation used for training.'}],
        'program_label_proposal': True,
    },
}

def author_identity(archive_member):
    match = re.fullmatch(r'(\d{4}-\d{2}-\d{2})-(nb_\d+)\.ipynb', Path(archive_member).name)
    if not match:
        raise ValueError('Unexpected notebook identifier')
    return 'GitHub-data/notebooks/' + match[1] + '/' + match[2] + '.py'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--partition',choices=['dev','test'],default='dev');args=parser.parse_args()
    if args.partition=='test' and not (ROOT/'runs/formal-real-neural-v1/predictions.json').exists():
        raise SystemExit('Held-out review waits until frozen predictions exist')
    private = ROOT.parent/'private-annotations'
    out=private/('development-review.json' if args.partition=='dev' else 'heldout-review.json')
    if out.exists():raise SystemExit('Refusing to overwrite existing student review: '+str(out))
    labels = {}
    for name in ('ground-truth.csv','manual-labels.csv'):
        rows = json.loads((private/(name+'.json')).read_text())['records']
        labels[name] = {r['nb']:r for r in rows}
        if len(labels[name]) != len(rows):
            raise ValueError('Duplicate full author path')
    records = []
    for r in json.loads((ROOT/'data/manifests/real.json').read_text()):
        if r['partition'] != ('dev' if args.partition=='dev' else 'test_pending_freeze'):
            continue
        identity = author_identity(r['archive_member'])
        source = ROOT/r['source_path']
        if digest(source.read_bytes()) != r['source_sha256']:
            raise ValueError('Review line references are stale')
        records.append({
            **{k:r[k] for k in ('sample_id','archive_member','source_path','source_sha256')},
            'author_identity':identity,
            'author_labels':{name:lookup[identity] for name,lookup in labels.items()},
            **NOTES.get(r['sample_id'],{'scope_proposal':'pending source inspection','events':[],'program_label_proposal':None}),
            'proposer':'AI-assisted code inspection, not independent human annotation',
            'review_status':'pending_student_review', 'reviewer':None,
            'reviewed_label':None, 'review_rationale':None,
        })
    write_json(out,records)
    print(str(out),len(records),args.partition+' records; original labels unchanged')

if __name__=='__main__':
    main()
