
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, Normalizer, scale
value_006 = pd.read_csv('features.csv')
value_010 = value_006['target']
value_005 = value_006.drop('target', axis=1)

def value_009(value_011, value_001):
    return value_007(value_011, value_001)

def value_007(value_011, value_001):
    return scale(value_011, axis=value_001)
value_005 = value_009(value_005, 0)
(value_000, value_002, value_003, value_004) = train_test_split(value_005, value_010, random_state=42)
value_008 = LogisticRegression()
value_008.fit(value_000, value_003)
value_008.predict(value_002)
