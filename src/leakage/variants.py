"""Semantics-preserving transformations restricted to controlled pure primitives."""
import ast
import copy
import astunparse

def rename(source):
    tree=ast.parse(source)
    local_functions={n.name:n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)}
    bound={n.id for n in ast.walk(tree) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)}
    bound|={n.arg for n in ast.walk(tree) if isinstance(n,ast.arg)}
    bound|=set(local_functions)
    mapping={name:'value_%03d'%i for i,name in enumerate(sorted(bound))}
    class Rename(ast.NodeTransformer):
        def visit_Name(self,n):
            n.id=mapping.get(n.id,n.id);return n
        def visit_arg(self,n):
            n.arg=mapping.get(n.arg,n.arg);return n
        def visit_FunctionDef(self,n):
            self.generic_visit(n);n.name=mapping.get(n.name,n.name);return n
        def visit_Call(self,n):
            local=isinstance(n.func,ast.Name) and n.func.id in local_functions
            self.generic_visit(n)
            if local:
                for k in n.keywords:k.arg=mapping.get(k.arg,k.arg)
            return n
    return astunparse.unparse(ast.fix_missing_locations(Rename().visit(tree)))

def wrap(source,depth=1):
    tree=ast.parse(source)
    definitions=[]
    class Wrap(ast.NodeTransformer):
        def visit_Call(self,node):
            self.generic_visit(node)
            primitive=isinstance(node.func,ast.Name) and node.func.id=='scale'
            primitive|=isinstance(node.func,ast.Attribute) and node.func.attr in {'mean','std','var','min','max','median','sum','prod','quantile'}
            if not primitive or any(isinstance(a,ast.Starred) for a in node.args) or any(k.arg is None for k in node.keywords):return node
            actual=([node.func.value] if isinstance(node.func,ast.Attribute) else [])+node.args+[k.value for k in node.keywords]
            parameters=['item_%d'%i for i in range(len(actual))]
            offset=1 if isinstance(node.func,ast.Attribute) else 0
            func=ast.Attribute(ast.Name(parameters[0],ast.Load()),node.func.attr,ast.Load()) if offset else copy.deepcopy(node.func)
            inner=ast.Call(func,[ast.Name(parameters[offset+i],ast.Load()) for i in range(len(node.args))],
                           [ast.keyword(k.arg,ast.Name(parameters[offset+len(node.args)+i],ast.Load())) for i,k in enumerate(node.keywords)])
            for layer in range(depth):
                name='_pure_wrapper_%d'%len(definitions)
                args=ast.arguments(posonlyargs=[],args=[ast.arg(p, annotation=None) for p in parameters],vararg=None,kwonlyargs=[],kw_defaults=[],kwarg=None,defaults=[])
                definitions.append(ast.FunctionDef(name,args,[ast.Return(inner)],[],returns=None,type_comment=None))
                inner=ast.Call(ast.Name(name,ast.Load()),[ast.Name(p,ast.Load()) for p in parameters],[])
            return ast.copy_location(ast.Call(ast.Name(name,ast.Load()),actual,[]),node)
    transformed=Wrap().visit(tree)
    transformed.body=definitions+transformed.body
    return astunparse.unparse(ast.fix_missing_locations(transformed))

def comments(source):
    return '\n'.join('# Formatting robustness marker.'+'\n'+line if i%4==0 else line for i,line in enumerate(source.splitlines()))+'\n'
