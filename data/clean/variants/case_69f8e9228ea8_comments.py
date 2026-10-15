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
def prepare(x, columnwise):
    if columnwise:
        return scale(x, axis=0)
# Formatting robustness marker.
    else:
        return scale(x, axis=1)
features = prepare(features, False)
a, b, c, d = train_test_split(features, target, random_state=42)
# Formatting robustness marker.
model = LogisticRegression()
model.fit(a, c)
model.predict(b)
