"""Evaluator only: this module may read labels; analyzer/model modules may not."""
from collections import Counter, defaultdict

SUCCESS = {'leak','no_finding'}

def ratio(a,b):
    return a/b if b else None

def metrics(predictions, labels, field='scope_status'):
    counts=Counter()
    known_positive=0
    for p in predictions:
        sid=p['sample_id']
        status=p.get(field,p['status'])
        if status not in SUCCESS | {'unknown','error','timeout'}:
            raise ValueError('Invalid analysis status: ' + str(status))
        counts[status]+=1
        if sid not in labels or labels[sid] is None:
            counts['unlabelled']+=1
            continue
        label=labels[sid]
        known_positive+=int(label)
        if status not in SUCCESS:
            continue
        counts['TP' if label and status=='leak' else 'FN' if label else 'FP' if status=='leak' else 'TN']+=1
    tp,fp,fn,tn=(counts[k] for k in ('TP','FP','FN','TN'))
    precision=ratio(tp,tp+fp)
    recall=ratio(tp,tp+fn)
    return {**{k:counts[k] for k in ('TP','FP','FN','TN','unknown','error','timeout','unlabelled')},
            'scheduled':len(predictions),'success':counts['leak']+counts['no_finding'],
            'labelled_success':tp+fp+fn+tn,
            'coverage':ratio(counts['leak']+counts['no_finding'],len(predictions)),
            'conditional_precision':precision,'conditional_recall':recall,
            'conditional_f1':ratio(2*tp,2*tp+fp+fn),
            'full_set_detection_recall':ratio(tp,known_positive)}

def compare(predictions,labels):
    groups=defaultdict(list)
    seen=set()
    for p in predictions:
        identity=(p['sample_id'],p['method'])
        if identity in seen:
            raise ValueError('Duplicate program-method prediction')
        seen.add(identity)
        groups[p['method']].append(p)
    cohorts={method:{p['sample_id'] for p in rows} for method,rows in groups.items()}
    if cohorts and any(ids!=next(iter(cohorts.values())) for ids in cohorts.values()):
        raise ValueError('Method cohorts differ; missing predictions cannot be silently omitted')
    by_sample=defaultdict(dict)
    for p in predictions:by_sample[p['sample_id']][p['method']]=p
    for sid,methods in by_sample.items():
        hashes={p.get('source_sha256') for p in methods.values()}
        if len(hashes)>1:
            raise ValueError('Methods analyzed different source content: '+sid)
        if 'N0' in methods and 'N1' in methods:
            a,b=methods['N0'],methods['N1']
            if a.get('summary_batch_sha256')!=b.get('summary_batch_sha256'):
                raise ValueError('N0/N1 did not replay the same saved summary batch: '+sid)
            if not a.get('summary_batch_sha256') and any(p['status'] in SUCCESS for p in (a,b)):
                raise ValueError('Successful neural mode has no recorded summary batch: '+sid)
    common=set.intersection(*({p['sample_id'] for p in rows if p.get('scope_status',p['status']) in SUCCESS} for rows in groups.values())) if groups else set()
    return {'primary_scope_projection':{m:metrics(rows,labels) for m,rows in groups.items()},
            'raw_upstream_scope':{m:metrics(rows,labels,'status') for m,rows in groups.items()},
            'common_success_count':len(common),
            'common_success_metrics':{m:metrics([p for p in rows if p['sample_id'] in common],labels) for m,rows in groups.items()},
            'zero_denominator':'null, not zero',
            'unknown_policy':'excluded from conditional confusion matrix; counted as not detected for full-set positive recall'}

