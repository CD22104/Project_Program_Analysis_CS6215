
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, Normalizer, scale
value_006 = pd.read_csv('features.csv')
value_009 = value_006['target']
value_005 = value_006.drop('target', axis=1)

def value_008(value_010, value_003):
    if value_003:
        return scale(value_010, axis=0)
    else:
        return scale(value_010, axis=1)
value_005 = value_008(value_005, True)
(value_000, value_001, value_002, value_004) = train_test_split(value_005, value_009, random_state=42)
value_007 = LogisticRegression()
value_007.fit(value_000, value_002)
value_007.predict(value_001)
