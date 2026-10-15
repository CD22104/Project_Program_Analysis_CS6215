import pytest
from leakage.evaluate import metrics, compare

def test_unknown_is_not_a_negative():
    rows=[{'sample_id':'a','status':'unknown'},{'sample_id':'b','status':'no_finding'},
          {'sample_id':'c','status':'error'},{'sample_id':'d','status':'leak'}]
    result=metrics(rows,{'a':True,'b':False,'c':False,'d':True})
    assert (result['TP'],result['FP'],result['FN'],result['TN'])==(1,0,0,1)
    assert result['conditional_recall']==1
    assert result['full_set_detection_recall']==.5
    assert result['coverage']==.5

def test_empty_denominator_is_null():
    assert metrics([{'sample_id':'a','status':'timeout'}],{'a':True})['conditional_precision'] is None

def test_missing_method_sample_is_an_error():
    rows=[{'sample_id':'a','method':'S0','status':'leak'}, {'sample_id':'b','method':'S1','status':'leak'}]
    with pytest.raises(ValueError):compare(rows,{'a':True,'b':True})

def test_unlabelled_subject_still_counts_towards_execution_coverage():
    rows=[{'sample_id':'a','status':'no_finding'}, {'sample_id':'b','status':'timeout'}]
    r=metrics(rows,{})
    assert r['success']==1 and r['coverage']==.5
    assert r['timeout']==1 and r['unlabelled']==2 and r['TN']==0
    assert r['conditional_f1'] is None

def test_different_neural_batches_are_not_a_verifier_comparison():
    rows=[{'sample_id':'a','method':m,'status':'no_finding','summary_batch_sha256':m} for m in ('N0','N1')]
    with pytest.raises(ValueError,match='same saved summary batch'):compare(rows,{'a':False})

def test_same_identifier_does_not_hide_changed_source():
    rows=[{'sample_id':'a','method':m,'status':'no_finding','source_sha256':m} for m in ('S0','S1')]
    with pytest.raises(ValueError,match='different source content'):compare(rows,{'a':False})
