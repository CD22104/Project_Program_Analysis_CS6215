"""Evaluator-only paired robustness, repetition, and model-evidence summaries."""
from collections import Counter, defaultdict
from .evaluate import SUCCESS, compare, ratio

def paired_variants(base, variants, labels):
    compare(base, labels)
    compare(variants, labels)
    base_by_id={(r['sample_id'],r['method']):r for r in base}
    counts=defaultdict(Counter)
    for row in variants:
        key=(row['base_sample_id'],row['method'])
        if key not in base_by_id:
            raise ValueError('Missing base prediction for paired variant')
        original=base_by_id[key]
        a=original.get('scope_status',original['status'])
        b=row.get('scope_status',row['status'])
        c=counts[row['method'],row['variant']]
        c['scheduled_pairs']+=1
        c['status_changes']+=int(a!=b)
        if a not in SUCCESS or b not in SUCCESS:
            c['incomplete_pairs']+=1
            continue
        c['successful_pairs']+=1
        c['binary_flips']+=int(a!=b)
        label=labels.get(row['base_sample_id'])
        if label is not None:
            if row['sample_id'] in labels and labels[row['sample_id']]!=label:
                raise ValueError('Variant label disagrees with its base')
            good_a=(a=='leak')==label
            good_b=(b=='leak')==label
            c['labelled_pairs']+=1
            c['base_correct']+=int(good_a)
            c['variant_correct']+=int(good_b)
            c['stable_wrong']+=int(not good_a and not good_b)
    return [{'method':m,'variant':v,**dict(c),
             'binary_flip_rate_conditional':ratio(c['binary_flips'],c['successful_pairs']),
             'status_change_rate_all':ratio(c['status_changes'],c['scheduled_pairs']),
             'paired_accuracy_delta':ratio(c['variant_correct']-c['base_correct'],c['labelled_pairs'])}
            for (m,v),c in sorted(counts.items())]

def repeated_predictions(replicates, expected_ids):
    if len(replicates)!=3:
        raise ValueError('The protocol requires exactly three generations')
    groups=defaultdict(list)
    methods=None
    for records in replicates:
        compare(records,{})
        current={r['method'] for r in records}
        if methods is not None and methods!=current:
            raise ValueError('Repeat methods differ')
        methods=current
        for method in methods:
            if {r['sample_id'] for r in records if r['method']==method}!=set(expected_ids):
                raise ValueError('Repeat cohort does not match the frozen subject list')
        for r in records:groups[r['method'],r['sample_id']].append(r.get('scope_status',r['status']))
    out=defaultdict(Counter)
    for (method,sid),statuses in groups.items():
        c=out[method];c['subjects']+=1
        c['all_status_agreement']+=int(len(set(statuses))==1)
        if all(s in SUCCESS for s in statuses):
            c['complete_subjects']+=1
            c['binary_agreement']+=int(len(set(statuses))==1)
        else:c['incomplete_subjects']+=1
    return {m:{**dict(c),'binary_agreement_rate_conditional':ratio(c['binary_agreement'],c['complete_subjects']),
               'all_status_agreement_rate':ratio(c['all_status_agreement'],c['subjects'])} for m,c in out.items()}

def model_evidence(batches, records, predictions):
    """Count actual records, never interpret fixtures as experimental inference."""
    compare(predictions,{})  # also checks matched N0/N1 batch identity
    keys={key for b in batches for key in b['records'].values()}
    if any(b.get('origin')!='live_api' for b in batches):
        raise ValueError('Non-live batch cannot supply model experiment evidence')
    if any(key not in records or records[key].get('origin')!='live_api' for key in keys):
        raise ValueError('Missing live raw record')
    totals=Counter();models=set();attempt_errors=Counter()
    newly_generated={key for b in batches for cid,key in b['records'].items() if not b['cache_hits'][cid]}
    for b in batches:
        totals['candidate_references']+=len(b['records'])
        totals['cache_hits']+=sum(b['cache_hits'].values())
        totals['generation_wall_seconds']+=b['generation_elapsed_seconds']
    for key in keys:
        record=records[key]
        totals['unique_records']+=1
        totals['parseable_summaries']+=int(record['summary'] is not None)
        totals['budget_exhausted_records']+=int(record.get('budget_exhausted',False))
        for attempt in record['attempts']:
            totals['historical_attempts']+=1
            if attempt.get('model_returned'):models.add(attempt['model_returned'])
            if not attempt['success']:attempt_errors[attempt.get('error_type','unknown')]+=1
            if key not in newly_generated:continue
            totals['new_request_attempts']+=1
            totals['new_request_seconds']+=attempt['elapsed_seconds']
            usage=attempt.get('usage') or {}
            if type(usage.get('total_tokens')) is int:
                totals['reported_total_tokens']+=usage['total_tokens']
                for field in ('prompt_tokens','completion_tokens'):
                    if type(usage.get(field)) is int:totals['reported_'+field]+=usage[field]
            else:totals['new_attempts_without_reported_usage']+=1
    checks=defaultdict(Counter)
    for p in predictions:
        for check in p.get('checks',[]):
            c=checks[p['method']];c['total']+=1
            c['accepted' if check['accepted'] else 'rejected']+=1
            c['fallback']+=int(bool(check.get('fallback')))
    return {'costs':dict(totals),'models_returned':sorted(models),'attempt_errors':dict(attempt_errors),
            'verification':{m:dict(c) for m,c in checks.items()},
            'summary_semantic_accuracy':'not automatically equated to rule agreement; human audit pending',
            'usage_policy':'missing usage is unknown, not zero; raw attempts and reservations retained'}
