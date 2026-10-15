import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, Normalizer, scale

frame = pd.read_csv("features.csv")
target = frame["target"]
features = frame.drop("target", axis=1)
def apply(x, state):
    return state.transform(x)
state = StandardScaler()
state.fit(features)
a, b, c, d = train_test_split(features, target, random_state=42)
a = apply(a, state)
b = apply(b, state)
model = LogisticRegression()
model.fit(a, c)
model.predict(b)
