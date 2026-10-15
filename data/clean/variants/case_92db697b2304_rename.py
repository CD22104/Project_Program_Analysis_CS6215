
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, Normalizer, scale
value_005 = pd.read_csv('features.csv')
value_008 = value_005['target']
value_004 = value_005.drop('target', axis=1)
(value_000, value_001, value_002, value_003) = train_test_split(value_004, value_008, random_state=42)
value_007 = value_000.sum(axis=0)
value_000 = (value_000 - value_007)
value_001 = (value_001 - value_007)
value_006 = LogisticRegression()
value_006.fit(value_000, value_002)
value_006.predict(value_001)
