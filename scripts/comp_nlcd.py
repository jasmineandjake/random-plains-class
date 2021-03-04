import numpy as np
import rasterio
from sklearn import metrics


def make_nlcd_array(raster_path):
    with rasterio.open(raster_path, "r") as ds:
        arr = ds.read().astype("float32")
    arr[arr == 0] = -9999
    arr[arr > 89] = 9
    arr[arr > 79] = 8
    arr[arr > 69] = 7
    arr[arr > 59] = 6
    arr[arr > 49] = 5
    arr[arr > 39] = 4
    arr[arr > 29] = 3
    arr[arr > 19] = 2
    arr[arr > 9] = 1
    return arr


def make_model_array(raster_path):
    with rasterio.open(raster_path, "r") as ds:
        arr = ds.read().astype("float32")
        # no_data = ds.nodatavals
    return arr


nlcd_raster_folder = "/home/jake/scripts/land_cover/nlcd_clipped_years/"
model_raster_folder = "/home/jake/scripts/land_cover/nan_holes_clipped_years/"

raster_name_list = [
    "grover_2001",
    "grover_2004",
    "grover_2006",
    "grover_2008",
    "grover_2011",
    "grover_2013",
    "grover_2016",
    "wellington_2001",
    "wellington_2004",
    "wellington_2006",
    "wellington_2008",
    "wellington_2011",
    "wellington_2013",
    "wellington_2016",
]

for raster_name in raster_name_list:
    nlcd_raster = f"{nlcd_raster_folder}{raster_name}.tif"
    model_raster = f"{model_raster_folder}{raster_name}.tif"

    nlcd_arr = make_nlcd_array(nlcd_raster)

    model_arr = make_model_array(model_raster)

    nlcd_arr[nlcd_arr == -9999] = np.nan
    model_arr[model_arr == -9999] = np.nan

    mask = ~np.isnan(model_arr).any(axis=0)
    nlcd_arr = nlcd_arr[:, mask]
    model_arr = model_arr[:, mask]

    nlcd = np.ravel(nlcd_arr).astype(int)
    model = np.ravel(model_arr).astype(int)

    accuracy_score = metrics.accuracy_score(nlcd, model)
    print("_____________{}_____________".format(raster_name))
    print("accuracy_score ", accuracy_score)
    # cm = metrics.confusion_matrix(nlcd, model)
    # print(cm.shape)
    # print('confusion_matrix \n', cm)
    # print('cm.diagonal() ', cm.diagonal())
    # print('cm.sum(axis=0) ', cm.sum(axis=0))
    # accuracy = cm.diagonal() / cm.sum(axis=0)
    # print(cm.sum(axis=0).reshape(1,8).shape)
    # print(accuracy.reshape(1,8).shape)
    # print("accuracy ", accuracy)
    # stack = np.vstack([cm, cm.sum(axis=0), accuracy]).reshape(10,8)
    # print(stack.shape)
    # #stack.tofile(f'{raster_name}.csv', sep = ',')
    # np.savetxt(f'{raster_name}.csv', stack, delimiter = ",")
    print("cohen_kappa_score ", metrics.cohen_kappa_score(nlcd, model))
