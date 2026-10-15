import pytest
from leakage.study import paired_variants,repeated_predictions

def prediction(sid,status,**extra):
    return {'sample_id':sid,'method':'S1','status':status,**extra}

def test_stable_wrong_is_not_called_correct_robustness():
    base=[prediction('a','no_finding'),prediction('b','leak')]
    variants=[prediction('a_r','no_finding',base_sample_id='a',variant='rename'),
              prediction('b_r','unknown',base_sample_id='b',variant='rename')]
    r=paired_variants(base,variants,{'a':True,'b':True})[0]
    assert r['stable_wrong']==1 and r['incomplete_pairs']==1
    assert r['binary_flip_rate_conditional']==0 and r['status_change_rate_all']==.5

def test_repeat_unknown_agreement_is_not_binary_success():
    runs=[[prediction('a','unknown')] for _ in range(3)]
    r=repeated_predictions(runs,['a'])['S1']
    assert r['all_status_agreement_rate']==1
    assert r['binary_agreement_rate_conditional'] is None

def test_missing_repeat_subject_is_an_error():
    runs=[[prediction('a','leak')] for _ in range(3)]
    with pytest.raises(ValueError):repeated_predictions(runs,['a','b'])
