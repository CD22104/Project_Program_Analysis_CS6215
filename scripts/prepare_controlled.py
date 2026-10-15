"""Deterministic paired subjects; labels are written only to evaluator storage."""
import ast
import random
from pathlib import Path
from leakage.common import ROOT, digest, write_json

HEADER = '''import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, Normalizer, scale

frame = pd.read_csv("features.csv")
target = frame["target"]
features = frame.drop("target", axis=1)
'''
SPLIT = 'a, b, c, d = train_test_split(features, target, random_state=42)\n'
END = 'model = LogisticRegression()\nmodel.fit(a, c)\nmodel.predict(b)\n'

def pair(i):
    if i == 0:
        return ['', 'features = features - features.mean(axis=0)\n' + SPLIT,
                'features = features.sub(features.mean(axis=1), axis=0)\n' + SPLIT]
    if i == 1:
        return ['def prepare(x, dimension):\n    return scale(x, axis=dimension)\n',
                'features = prepare(features, 0)\n' + SPLIT,
                'features = prepare(features, 1)\n' + SPLIT]
    if i == 2:
        return ['', 'features = features.fillna(features.mean())\n' + SPLIT,
                'features = features.fillna(0)\n' + SPLIT]
    if i == 3:
        return ['', 'state = StandardScaler()\nfeatures = state.fit_transform(features)\n' + SPLIT,
                SPLIT + 'state = StandardScaler()\nstate.fit(a)\na = state.transform(a)\nb = state.transform(b)\n']
    if i == 4:
        return ['def statistics(x):\n    return x.mean(axis=0)\n',
                'features = features - statistics(features)\n' + SPLIT,
                SPLIT + 'stats = statistics(a)\na = a - stats\nb = b - stats\n']
    if i == 5:
        return ['def prepare(x):\n    statistic = x.mean(axis=0)\n    return x - statistic\n',
                'features = prepare(features)\n' + SPLIT,
                'unused = prepare(features)\n' + SPLIT]
    if i == 6:
        return ['def prepare(x, dimension):\n    return scale(x, axis=dimension)\n',
                'unused = prepare(features, 1)\nfeatures = prepare(features, 0)\n' + SPLIT,
                'unused = prepare(features, 0)\nfeatures = prepare(features, 1)\n' + SPLIT]
    if i == 7:
        return ['def apply(x, state):\n    return state.transform(x)\n',
                'state = StandardScaler()\nstate.fit(features)\n' + SPLIT + 'a = apply(a, state)\nb = apply(b, state)\n',
                SPLIT + 'state = StandardScaler()\nstate.fit(a)\na = apply(a, state)\nb = apply(b, state)\n']
    # Additional distinct semantic cases are reserved for the later frozen test.
    reducers = {8: 'std', 9: 'var', 10: 'min', 11: 'max', 12: 'median', 13: 'sum',
                14: 'prod', 15: 'quantile'}
    if i in reducers:
        op = reducers[i]
        arg = '0.5, ' if op == 'quantile' else ''
        return ['', f'features = features - features.{op}({arg}axis=0)\n' + SPLIT,
                SPLIT + f'stats = a.{op}({arg}axis=0)\na = a - stats\nb = b - stats\n']
    if i == 16:
        return ['def outer(x, axis):\n    return inner(x, axis)\ndef inner(x, axis):\n    return scale(x, axis=axis)\n',
                'features = outer(features, 0)\n' + SPLIT, 'features = outer(features, 1)\n' + SPLIT]
    if i == 17:
        return ['from sklearn.feature_selection import SelectKBest\n',
                'selector = SelectKBest(k=1)\nfeatures = selector.fit_transform(features, target)\n' + SPLIT,
                SPLIT + 'selector = SelectKBest(k=1)\nselector.fit(a, c)\na = selector.transform(a)\nb = selector.transform(b)\n']
    if i == 18:
        return ['', 'features = scale(features, axis=0)\n' + SPLIT, 'features = scale(features, axis=1)\n' + SPLIT]
    if i == 19:
        return ['', 'unused = features.mean()\nfeatures = features.fillna(features.median())\n' + SPLIT,
                'unused = features.mean()\nfeatures = features.fillna(3)\n' + SPLIT]
    if i == 20:
        return ['def prepare(x, columnwise):\n    if columnwise:\n        return scale(x, axis=0)\n    else:\n        return scale(x, axis=1)\n',
                'features = prepare(features, True)\n' + SPLIT, 'features = prepare(features, False)\n' + SPLIT]
    if i == 21:
        return ['', SPLIT + 'stats = pd.concat([a, b]).mean()\na = a - stats\nb = b - stats\n',
                SPLIT + 'stats = a.mean()\na = a - stats\nb = b - stats\n']
    if i == 22:
        return ['', SPLIT + 'state = StandardScaler()\nstate.fit(a)\nstate.fit(b)\na = state.transform(a)\nb = state.transform(b)\n',
                SPLIT + 'state = StandardScaler()\nstate.fit(a)\na = state.transform(a)\nb = state.transform(b)\n']
    return ['', 'state = StandardScaler()\nfeatures = state.fit_transform(features)\n' + SPLIT,
            SPLIT + 'state = StandardScaler()\na = state.fit_transform(a)\nb = state.fit_transform(b)\n']

def main():
    # Families 0–7 are predeclared development semantics (including six required
    # pilot pairs). Family sampling is not chosen by observed analyzer outcomes.
    # The original plan's randomized 8/16 split is replaced with this declared
    # semantic split BEFORE any held-out execution. This change must be reviewed.
    manifest, labels = [], []
    for i in range(24):
        definitions, p, n = pair(i)
        for side, body in enumerate((p, n)):
            source = HEADER + definitions + body + END
            ast.parse(source)
            sid = 'case_' + digest('6215:' + str(i) + ':' + str(side))[:12]
            path = ROOT / 'data/clean/controlled' / (sid + '.py')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source)
            family = 'F%02d' % i
            manifest.append({'sample_id': sid, 'family': family, 'partition': 'dev' if i < 8 else 'test_pending_freeze',
                             'source_kind': 'controlled', 'variant': 'base', 'source_path': str(path.relative_to(ROOT)),
                             'source_sha256': digest(source), 'assumptions': {'sample_axis': 0, 'input_rank': 2},
                             'label_review_status': 'pending_student_review'})
            labels.append({'sample_id': sid, 'label': side == 0, 'family': family,
                           'review_status': 'pending_student_review', 'basis': 'generator construction; student must verify'})
    write_json(ROOT / 'data/manifests/controlled.json', manifest)
    write_json(ROOT / 'data/annotations/controlled.json', labels)
    print('Prepared 48 base programs in 24 semantic families; 16 development programs; 32 held out pending freeze.')

if __name__ == '__main__':
    main()
