import glob
import os

import numpy as np
import rasterio
from affine import Affine
from pyproj import CRS


def make_raster_stack_no_clip(folder_path):
    glob_str = os.path.join(folder_path, "*.tif")
    raster_list = sorted(glob.glob(glob_str))
    print(raster_list)
    stack_array = []
    for i, raster in enumerate(raster_list):
        with rasterio.open(raster, "r") as ds:
            arr = ds.read().astype("float32")
            no_data = ds.nodatavals
        arr[arr == no_data] = np.nan
        stack_array.append(arr[0, :, :])
        print(
            "{} has {} nan, shape is {}\
              ".format(
                raster, np.count_nonzero(np.isnan(arr)), arr.shape
            )
        )
    return np.array(stack_array)


outputs_folder = "/home/jake/scripts/land_cover/nan_years"

arr = make_raster_stack_no_clip(outputs_folder)

crs = CRS.from_wkt(
    'PROJCS["Albers_Conical_Equal_Area",GEOGCS["WGS 84",DATUM["WGS_1984",\
     SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],\
     AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,\
     AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],\
     PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["latitude_of_center",23],\
     PARAMETER["longitude_of_center",-96],PARAMETER["standard_parallel_1",29.5],\
     PARAMETER["standard_parallel_2",45.5],PARAMETER["false_easting",0],\
     PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],\
     AXIS["Easting",EAST],AXIS["Northing",NORTH]]'
)

transform = Affine(30.0, 0.0, -833925.0, 0.0, -30.0, 2094465.0)

first_year = 1986
last_year = 2017
for arr_ind, year in enumerate(range(first_year, last_year + 1, 1)):
    print("running {}".format(year))
    output = np.empty((5784, 7585))
    output.fill(-9999)
    for i in range(5784):
        for j in range(7585):
            old = [arr[arr_ind, i, j], arr[arr_ind + 1, i, j], arr[arr_ind + 2, i, j]]
            new = [
                arr[arr_ind + 2, i, j],
                arr[arr_ind + 3, i, j],
                arr[arr_ind + 4, i, j],
            ]
            old_count = max(map(lambda val: (old.count(val), val), set(old)))
            new_count = max(map(lambda val: (new.count(val), val), set(new)))
            if old_count[0] > 1.5 and new_count[0] > 1.5:
                output[i, j] = int(10 * old_count[1] + new_count[1])

    with rasterio.open(
        f"/home/jake/scripts/land_cover/transitions/{year}.tif",
        "w",
        driver="GTiff",
        width=7585,
        height=5784,
        count=1,
        dtype=np.int16,
        nodata=-9999,
        transform=transform,
        crs=crs,
    ) as out:
        out.write_band(1, output.astype(np.int16))
