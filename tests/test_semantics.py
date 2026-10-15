"""Adversarial regression fixtures; these are not model experiment results."""
import copy
import json
from pathlib import Path
import pytest
from leakage.effects import proposed_summary, verify, primitive_effect, Frontend, UNKNOWN
from leakage.model import messages, cache_key, Budget
from leakage.projection import train_affecting
from leakage.sanitize import clean_source, extract_notebook

@pytest.fixture
def candidate():
    return {'candidate_id':'a'*64,'source_sha256':'b'*64,'ir_sha256':'c'*64,
            'invocation':'$invo4','context':'[, $invo5]','function_id':'prepare',
            'canonical_method':'sklearn.preprocessing.scale','code':'return scale(x, axis=dimension)',
            'ir_line':32,'input_variable':'x','input_index':1,'return_variable':'_var4',
            'receiver':None,'state_version':None,'resolved_axis':1,'input_rank':2,'sample_axis':0,
            'primitive_spec_sha256':'d'*64,'deterministic_effect':'row_preserving',
            'proof_reason':'literal axis=1 excludes sample axis 0'}

def test_false_safe_summary_rejected_by_n1_but_not_n0(candidate):
    candidate['deterministic_effect'] = 'cross_row_reduce'
    candidate['resolved_axis'] = 0
    summary = proposed_summary(candidate)
    summary['effects'][0]['kind'] = 'row_preserving'
    assert verify(candidate, summary, semantic=False)['accepted']
    assert not verify(candidate, summary, semantic=True)['accepted']

@pytest.mark.parametrize('field,value', [('context','[, $invo99]'),('source_sha256','f'*64),('ir_sha256','e'*64)])
def test_call_and_source_isolation(candidate, field, value):
    summary = proposed_summary(candidate)
    summary[field] = value
    assert not verify(candidate, summary, semantic=False)['accepted']

def test_unknown_axis_cannot_remove_conservative_effect(candidate):
    candidate['deterministic_effect'] = 'unknown'
    candidate['resolved_axis'] = 'unresolved'
    s = proposed_summary(candidate)
    s['effects'][0]['kind'] = 'row_preserving'
    assert not verify(candidate, s)['accepted']

def test_stale_object_state_rejected(candidate):
    candidate.update(receiver='scale_0',state_version='$invo7:[, ]',deterministic_effect='fit_state')
    s = proposed_summary(candidate)
    s['effects'][0]['state_version'] = '$invo8:[, ]'
    assert not verify(candidate, s, semantic=False)['accepted']

def test_stale_primitive_specification_rejected(candidate):
    s = proposed_summary(candidate)
    s['primitive_spec_sha256'] = 'f'*64
    assert not verify(candidate, s, semantic=False)['accepted']

@pytest.mark.parametrize('method,rank,axis,params,expected', [
    ('numpy.mean',2,-1,{},'row_preserving'),
    ('numpy.mean',2,-2,{},'cross_row_reduce'),
    ('numpy.mean',2,2,{},'unknown'),
    ('DataFrame.mean',2,-1,{},'unknown'),
    ('DataFrame.mean',2,'columns',{},'row_preserving'),
    ('Series.mean',1,'columns',{},'unknown'),
    ('sklearn.preprocessing.scale',2,-1,{},'unknown'),
    ('sklearn.preprocessing.scale',2,0,{'with_mean':False,'with_std':False},'row_preserving'),
    ('sklearn.preprocessing.scale',2,0,{'with_std':UNKNOWN},'unknown'),
    ('sklearn.preprocessing.scale',2,1,{'copy':False},'unknown'),
    ('numpy.mean',2,1,{'out':'buffer'},'unknown'),
    ('numpy.quantile',2,1,{'q':UNKNOWN},'unknown'),
])
def test_api_parameters_do_not_prove_invalid_or_unsupported_calls_safe(method,rank,axis,params,expected):
    assert primitive_effect(method,rank,axis,params)[0] == expected

def test_quantile_axis_is_not_its_probability_argument():
    front = Frontend.__new__(Frontend)
    front.keywords = {}
    front.actual = {('i',1):'data',('i',2):'half',('i',3):'column'}
    front.constants = {('half','ctx'):{('float',0.5)},('column','ctx'):{('int',1)}}
    axis, params = front.primitive_arguments('i','ctx','numpy.quantile',False)
    assert axis == 1 and params['q'] == 0.5
    assert primitive_effect('numpy.quantile',2,axis,params)[0] == 'row_preserving'

def test_model_input_allowlist(candidate):
    candidate.update(label=True, raw_preprocessing_rows=['SECRET_WARNING'], proof_reason='SECRET_PROOF', author_html='SECRET_HTML')
    payload = json.dumps(messages(candidate))
    assert 'SECRET_' not in payload
    assert 'raw_preprocessing_rows' not in payload
    assert 'deterministic_effect' not in payload

def test_cache_tracks_context_axis_model_prompt_and_replicate(candidate):
    cfg={'SOCLAAS_MODEL':'model-a','SOCLAAS_BASE_URL':'https://soclaas-api.comp.nus.edu.sg/v1'}
    key=cache_key(candidate,cfg)
    for field,val in [('context','[, $invo9]'),('resolved_axis',0),('source_sha256','e'*64)]:
        other={**candidate,field:val}
        assert cache_key(other,cfg)!=key
    assert cache_key(candidate,{**cfg,'SOCLAAS_MODEL':'model-b'})!=key
    assert cache_key(candidate,cfg,repeat=1)!=key

def test_budget_includes_failed_attempt_reservations(tmp_path):
    b=Budget(tmp_path/'ledger.jsonl',100)
    b.reserve(60,'request-a')
    with pytest.raises(ValueError): b.reserve(41,'request-a-retry')

def test_reported_usage_releases_only_unused_reservation(tmp_path):
    b=Budget(tmp_path/'ledger.jsonl',100)
    b.reserve(80,'request-a')
    b.settle(80,20,'request-a')
    b.reserve(80,'request-b')
    with pytest.raises(ValueError):b.reserve(1,'request-c')

def test_sanitization_ignores_output_markdown_and_conclusion_comments():
    notebook={'cells':[{'cell_type':'markdown','source':['SECRET_LABEL']},
                       {'cell_type':'code','source':['x=1 # SECRET_COMMENT\n'],'outputs':[{'text':'SECRET_OUTPUT'}]}]}
    code,mapping=extract_notebook(notebook)
    assert 'SECRET' not in code
    assert mapping==[{'line':1,'cell_index':1,'cell_line':1}]

def test_inline_docstring_keeps_following_statement():
    import ast
    code=clean_source('def f(): "SECRET"; return 1\n')
    assert 'SECRET' not in code
    assert isinstance(ast.parse(code).body[0].body[1],ast.Return)

def test_multiline_docstring_keeps_line_mapping():
    import ast
    source='def f():\n    """SECRET\n    SECRET"""\n    return 1\n'
    code=clean_source(source)
    assert 'SECRET' not in code
    assert ast.parse(code).body[0].body[-1].lineno==4

def test_scope_projection_does_not_join_wrong_call_context(tmp_path):
    def save(name,rows):
        (tmp_path/name).write_text(''.join('\t'.join(r)+'\n' for r in rows))
    telemetry=['model','train','fit','M.fit','[, ]','model','test','pred','M.predict','[, ]','reduced','source']
    save('Telemetry_FinalPreProcessingLeak.csv',[telemetry])
    save('FlowFromExtended.csv',[['train','[, ]','reduced','[, correct]','data']])
    save('DataOverlap.csv',[['test','[, ]','source','[, wrong]']])
    save('TaintStartsTarget.csv',[['reduced','[, wrong]','source','[, wrong]','i','mean','rowset']])
    assert train_affecting(tmp_path)==[]
    save('TaintStartsTarget.csv',[['reduced','[, correct]','source','[, wrong]','i','mean','rowset']])
    assert train_affecting(tmp_path)==[telemetry]
