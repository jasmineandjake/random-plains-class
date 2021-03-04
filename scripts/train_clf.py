import os
import time

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

y_train = np.load("training_labels8_all.npy")
X_train = np.load("training_objects8_all.npy")
rng = 123

print("Fitting Random Forest Classifier")

d = {
    "class_weight": "balanced",
    "criterion": "entropy",
    "max_features": 10,
    "min_samples_split": 2,
    "n_estimators": 200,
}
classifier = RandomForestClassifier(
    n_jobs=7,
    class_weight=d["class_weight"],
    criterion=d["criterion"],
    max_features=d["max_features"],
    min_samples_split=d["min_samples_split"],
    n_estimators=d["n_estimators"],
    random_state=rng,
    verbose=5,
)

t0 = time.time()
classifier.fit(X_train, y_train)
t1 = time.time()

total = t1 - t0
print("classifier fitting took ", total)

print(classifier.feature_importances_)

if os.path.exists("randomforest_full_8.sav"):
    os.remove("randomforest_full_8.sav")
joblib.dump(classifier, "randomforest_full_8.sav")

print("model save finished")
