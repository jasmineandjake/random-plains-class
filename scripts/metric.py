import joblib
import numpy as np
from sklearn import metrics

clf = joblib.load("randomforest_full_8.sav")
X_test = np.load("X_test8_all_sub.npy")
y_test = np.load("y_test8_all_sub.npy")

print(y_test.shape)
print(X_test.shape)

predicted = clf.predict(X_test)

cm = metrics.confusion_matrix(y_test, predicted)

print("confusion_matrix \n", cm)

print("cm.diagonal() ", cm.diagonal())
print("cm.sum(axis=0) ", cm.sum(axis=0))

accuracy = cm.diagonal() / cm.sum(axis=0)
print("accuracy ", accuracy)

print("accuracy_score ", metrics.accuracy_score(y_test, predicted))
print("macro metrics.f1_score ", metrics.f1_score(y_test, predicted, average="macro"))
print("micro metrics.f1_score ", metrics.f1_score(y_test, predicted, average="micro"))
print(
    "macro metrics.jaccard_score ",
    metrics.jaccard_score(y_test, predicted, average="macro"),
)
print(
    "micro metrics.jaccard_score ",
    metrics.jaccard_score(y_test, predicted, average="micro"),
)
print(
    "metrics.classification_report \n", metrics.classification_report(y_test, predicted)
)
print(
    "metrics.precision_score ",
    metrics.precision_score(y_test, predicted, average="macro"),
)
print("metrics.recall_score ", metrics.recall_score(y_test, predicted, average="micro"))
print(
    "metrics.fbeta_score ",
    metrics.fbeta_score(y_test, predicted, average="macro", beta=0.5),
)
