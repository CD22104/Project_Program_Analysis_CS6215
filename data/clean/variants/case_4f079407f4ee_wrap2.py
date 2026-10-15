

def _pure_wrapper_0(item_0, item_1):
    return item_0.prod(axis=item_1)

def _pure_wrapper_1(item_0, item_1):
    return _pure_wrapper_0(item_0, item_1)
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, Normalizer, scale
frame = pd.read_csv('features.csv')
target = frame['target']
features = frame.drop('target', axis=1)
features = (features - _pure_wrapper_1(features, 0))
(a, b, c, d) = train_test_split(features, target, random_state=42)
model = LogisticRegression()
model.fit(a, c)
model.predict(b)
