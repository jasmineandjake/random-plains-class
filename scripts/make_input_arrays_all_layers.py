import glob
import os
import pickle
import time
from operator import itemgetter

import numpy as np
import rasterio
from imblearn.under_sampling import NeighbourhoodCleaningRule, RandomUnderSampler
from osgeo import gdal
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


def make_raster_stack(folder_path):
    glob_str = os.path.join(folder_path, "*.tif")
    raster_list = sorted(glob.glob(glob_str))
    stack_array = []
    for i, raster in enumerate(raster_list):
        with rasterio.open(raster, "r") as ds:
            arr = ds.read()
        low = np.nanpercentile(arr, 0.5)
        high = np.nanpercentile(arr, 99.5)
        processed_array = np.clip(arr, low, high)
        processed_array = arr
        stack_array.append(processed_array[0, :, :])
        print(
            "{} has {} nan, low is {}, high is {}".format(
                raster, np.count_nonzero(np.isnan(processed_array)), low, high
            )
        )
        print(type(processed_array))
        print(processed_array.shape)
    return np.array(stack_array)


def loop_translate(a, d):
    n = np.ndarray(a.shape)
    for k in d:
        n[a == k] = int(d[k])
    return n


def get_class_count(y_train, N):
    segments = y_train

    segments_per_class = {}

    print(classes)

    klass_count_dict = {}
    for klass in classes:
        segments_of_class = segments[y_train == klass]
        segments_per_class[klass] = set(segments_of_class)
        print("Segments for class", klass, ":", len(segments_of_class))
        klass_count_dict[klass] = len(segments_of_class)
    res = sorted(klass_count_dict.items(), key=itemgetter(1), reverse=True)[N][1]
    print("res", res)
    print("sorted", sorted(klass_count_dict.items(), key=itemgetter(1), reverse=True))
    for key in klass_count_dict:
        if klass_count_dict[key] > res:
            klass_count_dict[key] = res
    return klass_count_dict


def get_class_count_value(y_train, value):
    segments = y_train

    segments_per_class = {}

    print(classes)

    klass_count_dict = {}
    for klass in classes:
        segments_of_class = segments[y_train == klass]
        segments_per_class[klass] = set(segments_of_class)
        print("Segments for class", klass, ":", len(segments_of_class))
        klass_count_dict[klass] = len(segments_of_class)
    print("sorted", sorted(klass_count_dict.items(), key=itemgetter(1), reverse=True))
    for key in klass_count_dict:
        if klass_count_dict[key] > value:
            klass_count_dict[key] = value
    return klass_count_dict


reclass_dict = {
    11: 1,
    12: 1,
    21: 2,
    22: 2,
    23: 2,
    24: 2,
    31: 3,
    41: 4,
    42: 4,
    43: 4,
    52: 5,
    71: 7,
    81: 8,
    82: 8,
    90: 9,
    95: 9,
}
X_train_list, X_test_list, y_train_list, y_test_list = [], [], [], []

rng = 123
value = 2205882

years = ["2001", "2004", "2006", "2008", "2011", "2013", "2016"]
for year in years:
    nlcd_path = (
        f"/media/desktop-linux/my_book/{year}_imagery/finished/nlcd/nlcd_{year}.tif"
    )
    truth_ds = gdal.Open(nlcd_path, gdal.GA_ReadOnly)
    initial_truth = truth_ds.GetRasterBand(1).ReadAsArray()

    print("initial classes ", np.unique(initial_truth))
    ground_truth = loop_translate(initial_truth, reclass_dict)

    classes = np.unique(ground_truth)
    print("translated class values", classes)

    folder_path = f"/media/desktop-linux/my_book/{year}_imagery/finished/all_layers"

    arr = make_raster_stack(folder_path)

    print(type(arr))
    print(arr.shape)
    mask = ~np.isnan(arr).any(axis=0)

    ground_truth = ground_truth[mask]
    arr = arr[:, mask]

    input_arr = np.swapaxes(arr, 0, 1)

    X_train, X_test, y_train, y_test = train_test_split(
        input_arr, ground_truth, test_size=0.5, random_state=rng, shuffle=True
    )
    X_remove, X_test, y_remove, y_test = train_test_split(
        X_test, y_test, test_size=0.00402228873, random_state=rng, shuffle=True
    )
    X_remove, y_remove = np.nan, np.nan

    rus = NeighbourhoodCleaningRule(
        n_jobs=7, n_neighbors=8, threshold_cleaning=0.2, sampling_strategy="all"
    )
    X_train, y_train = rus.fit_resample(X_train, y_train)

    dict = get_class_count_value(y_train, 1470588)
    print(year, " pre resample ", dict)

    rus = RandomUnderSampler(random_state=rng, sampling_strategy=dict)
    X_train, y_train = rus.fit_resample(X_train, y_train)

    X_train_list.append(X_train)
    X_test_list.append(X_test)
    y_train_list.append(y_train)
    y_test_list.append(y_test)

print("finished years for loop")

X_train_array = X_train_list[0]
for X_train in X_train_list[1:]:
    X_train_array = np.concatenate((X_train_array, X_train), axis=0)

X_test_array = X_test_list[0]
for X_test in X_test_list[1:]:
    X_test_array = np.concatenate((X_test_array, X_test), axis=0)

y_train_array = y_train_list[0]
for y_train in y_train_list[1:]:
    y_train_array = np.concatenate((y_train_array, y_train), axis=0)

y_test_array = y_test_list[0]
for y_test in y_test_list[1:]:
    y_test_array = np.concatenate((y_test_array, y_test), axis=0)

print("finished concatenates")

X_train, X_test, y_train, y_test = (
    X_train_array,
    X_test_array,
    y_train_array,
    y_test_array,
)
X_train_array, X_test_array, y_train_array, y_test_array = (
    np.nan,
    np.nan,
    np.nan,
    np.nan,
)


X_test_name = "X_test8_all_sub.npy"
if os.path.exists(X_test_name):
    os.remove(X_test_name)
np.save(X_test_name, X_test)
X_test = np.nan

y_test_name = "y_test8_all_sub.npy"
if os.path.exists(y_test_name):
    os.remove(y_test_name)
np.save(y_test_name, y_test)
y_test = np.nan

print("finished saving test")

rus = NeighbourhoodCleaningRule(
    n_jobs=7, n_neighbors=5, threshold_cleaning=0.35, sampling_strategy="all"
)
t0 = time.time()
X_train, y_train = rus.fit_resample(X_train, y_train)

dict = get_class_count_value(y_train, value)

print("final pre resample", dict)

rus = RandomUnderSampler(random_state=rng, sampling_strategy=dict)

X_train, y_train = rus.fit_resample(X_train, y_train)

t1 = time.time()

total = t1 - t0
print("under sampling took ", total)

segments = y_train

segments_per_class = {}

print(classes)

klass_count_dict = {}
for klass in classes:
    segments_of_class = segments[y_train == klass]
    segments_per_class[klass] = set(segments_of_class)
    print("Segments for class", klass, ":", len(segments_of_class))
    klass_count_dict[klass] = len(segments_of_class)

if os.path.exists("training_objects8_all.npy"):
    os.remove("training_objects8_all.npy")
np.save("training_objects8_all.npy", X_train)

if os.path.exists("training_labels8_all.npy"):
    os.remove("training_labels8_all.npy")
np.save("training_labels8_all.npy", y_train)

print("finished saving training arrays")

print("Fitting Random Forest Classifier")

d = {
    "class_weight": "balanced",
    "criterion": "entropy",
    "max_features": 10,
    "min_samples_split": 2,
    "n_estimators": 100,
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
pickle.dump(classifier, open("randomforest_full_8.sav", "wb"))

print("model save finished")
