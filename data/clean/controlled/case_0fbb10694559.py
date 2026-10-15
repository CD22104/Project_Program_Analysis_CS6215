import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, Normalizer, scale

frame = pd.read_csv("features.csv")
target = frame["target"]
features = frame.drop("target", axis=1)
from sklearn.feature_selection import SelectKBest
a, b, c, d = train_test_split(features, target, random_state=42)
selector = SelectKBest(k=1)
selector.fit(a, c)
a = selector.transform(a)
b = selector.transform(b)
model = LogisticRegression()
model.fit(a, c)
model.predict(b)
