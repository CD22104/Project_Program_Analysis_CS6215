

def _pure_wrapper_0(item_0, item_1):
    return item_0.max(axis=item_1)
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, Normalizer, scale
frame = pd.read_csv('features.csv')
target = frame['target']
features = frame.drop('target', axis=1)
(a, b, c, d) = train_test_split(features, target, random_state=42)
stats = _pure_wrapper_0(a, 0)
a = (a - stats)
b = (b - stats)
model = LogisticRegression()
model.fit(a, c)
model.predict(b)
