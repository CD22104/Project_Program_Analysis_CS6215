import ast
from leakage.variants import rename,wrap,comments

def test_rename_keeps_external_keywords_but_updates_local_keywords():
    source='def f(x, axis):\n return scale(x, axis=axis)\ny=f(data, axis=1)\n'
    tree=ast.parse(rename(source));calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
    external=next(n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='scale')
    local=next(n for n in calls if n is not external)
    assert external.keywords[0].arg=='axis'
    assert local.keywords[0].arg!='axis'

def test_wrapper_preserves_receiver_and_positional_keyword_binding():
    tree=ast.parse(wrap('y = data.mean(axis=1)\n',2))
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
    assert len(functions)==2
    inner=functions[0].body[0].value
    assert inner.func.attr=='mean' and inner.keywords[0].arg=='axis'
    outer_call=tree.body[-1].value
    assert isinstance(outer_call.args[0],ast.Name) and outer_call.args[0].id=='data'
    assert outer_call.args[1].value==1

def test_comments_do_not_change_ast():
    source='x = 1\ny = x + 2\n'
    assert ast.dump(ast.parse(source))==ast.dump(ast.parse(comments(source)))
