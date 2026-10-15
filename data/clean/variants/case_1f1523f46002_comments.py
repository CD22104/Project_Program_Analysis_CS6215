# Formatting robustness marker.
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
# Formatting robustness marker.
from sklearn.preprocessing import StandardScaler, Normalizer, scale

frame = pd.read_csv("features.csv")
target = frame["target"]
# Formatting robustness marker.
features = frame.drop("target", axis=1)
def outer(x, axis):
    return inner(x, axis)
def inner(x, axis):
# Formatting robustness marker.
    return scale(x, axis=axis)
features = outer(features, 0)
a, b, c, d = train_test_split(features, target, random_state=42)
model = LogisticRegression()
# Formatting robustness marker.
model.fit(a, c)
model.predict(b)
