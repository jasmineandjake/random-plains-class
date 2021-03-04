import pickle

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import GridSearchCV

X_train = np.load("training_objects8_all.npy")
y_train = np.load("training_labels8_all.npy")
n = 8
rng = 123

print("starting grid_search")
model = RandomForestClassifier()
param_grid = {
    "n_estimators": [10, 55, 100, 200],
    "max_features": [10],
    "criterion": ["entropy"],
    "class_weight": ["balanced"],
    "min_samples_split": [2],
}
grid_search = GridSearchCV(model, param_grid, cv=2, n_jobs=4, verbose=5)
grid_search.fit(X_train, y_train)

print("for {}: ".format(n), grid_search.best_params_)

d = grid_search.best_params_
grid_search = np.nan

clf = RandomForestClassifier(
    n_jobs=7,
    max_features=d["max_features"],
    min_samples_split=d["min_samples_split"],
    n_estimators=d["n_estimators"],
    criterion=d["criterion"],
    class_weight=d["class_weight"],
    random_state=rng,
    verbose=5,
)
print("starting fit")
clf.fit(X_train, y_train)

X_train, y_train = np.nan, np.nan

print("fit finished")

X_test = np.load("X_test8_all_sub.npy")

y_pred = clf.predict(X_test)
X_test = np.nan

print("pred finished")

filename = "randomforest_full_{}.sav".format(n)
pickle.dump(clf, open(filename, "wb"))
clf = np.nan

print("model saved")

y_test = np.load("y_test8_all_sub.npy")

print("metrics.classification_report \n", classification_report(y_test, y_pred))
print("micro metrics.f1_score ", f1_score(y_test, y_pred, average="micro"))
