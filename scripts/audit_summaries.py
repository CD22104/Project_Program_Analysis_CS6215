"""Post-generation, evaluator-only comparison against shared rules, not human gold."""
import json,csv
from collections import Counter
from leakage.common import ROOT,write_json
from rebuild_all import COHORTS

def main():
    rows=[]
    for cohort,(run,gen,_) in COHORTS.items():
        folder=ROOT/'runs'/run
        if not (folder/'predictions.json').exists():continue
        pred=json.loads((folder/'predictions.json').read_text())
        by={(p['sample_id'],p['method']):p for p in pred}
        for f in sorted((ROOT/'runs'/gen).glob('*.json')):
            if f.name=='generation-manifest.json':continue
            sid=f.stem;batch=json.loads(f.read_text());cp=folder/sid/'S1/candidates.json'
            if not cp.exists():continue
            for c in json.loads(cp.read_text()):
                cid=c['candidate_id'];s=batch['summaries'].get(cid)
                checks={m:next(x for x in by[sid,m]['checks'] if x['candidate_id']==cid) for m in ('N0','N1')}
                model_kinds=sorted(e['kind'] for e in s.get('effects',[])) if isinstance(s,dict) else []
                expected=c['deterministic_effect']
                rows.append({'cohort':cohort,'sample_id':sid,'candidate_id':cid,'canonical_method':c['canonical_method'],'rule_effect':expected,'proposed_effects':model_kinds,'N0_accepted':checks['N0']['accepted'],'N1_accepted':checks['N1']['accepted'],'N1_reason':checks['N1']['reason'],'rule_proof_reason':c['proof_reason'],'row_preserving_against_cross_row_rule':expected in ('cross_row_reduce','fit_state') and 'row_preserving' in model_kinds,'review_status':'rule-relative audit; independent student semantic review pending'})
    write_json(ROOT/'results/study/summary-audit.json',rows)
    counts=Counter((r['cohort'],str(r['rule_effect']),','.join(r['proposed_effects']),r['N1_accepted']) for r in rows)
    write_json(ROOT/'results/study/summary-audit-counts.json',[{'cohort':c,'rule_effect':rule,'proposed_effects':prop,'N1_accepted':a,'count':n} for (c,rule,prop,a),n in sorted(counts.items())])
    print('Audited',len(rows),'candidate proposals against deterministic rules; no human accuracy claim.')

if __name__=='__main__':main()
