import glob
import os
import time

import joblib
import numpy as np
import rasterio
from affine import Affine
from pyproj import CRS


def make_raster_stack(folder_path):
    glob_str = os.path.join(folder_path, "*.tif")
    raster_list = sorted(glob.glob(glob_str))
    stack_array = []
    for i, raster in enumerate(raster_list):
        with rasterio.open(raster, "r") as ds:
            arr = ds.read()
        low = np.nanpercentile(arr, 0.1)
        high = np.nanpercentile(arr, 99.9)
        processed_array = np.clip(arr, low, high)
        processed_array = arr
        stack_array.append(processed_array[0, :, :])
        print(
            "{} has {} nan, low is {}, high is {}, shape is {}\
              ".format(
                raster,
                np.count_nonzero(np.isnan(processed_array)),
                low,
                high,
                processed_array.shape,
            )
        )
    return np.array(stack_array)


clf = joblib.load("/home/jake/scripts/land_cover/randomforest_full_8.sav")

for year in [
    1984,
    1987,
    1990,
    1993,
    1996,
    1999,
    2002,
    2005,
    2008,
    2011,
    2014,
    2017,
    1986,
    1989,
    1992,
    1995,
    1998,
    2001,
    2004,
    2007,
    2010,
    2013,
    2016,
    2019,
    1985,
    1988,
    1991,
    1994,
    1997,
    2000,
    2003,
    2006,
    2009,
    2012,
    2015,
    2018,
]:
    print(f"starting {year}")
    t_start = time.time()
    folder_path = f"/media/jake/my_book/predict_imagery/{year}_imagery/finished"
    #
    year_stack_name = f"{year}_folder_path"

    arr = make_raster_stack(folder_path)

    mask = ~np.isnan(arr).any(axis=0)
    arr = arr[:, mask]
    input_arr = np.swapaxes(arr, 0, 1)

    t0 = time.time()
    predicted = clf.predict(input_arr)
    t1 = time.time()

    total = t1 - t0
    print("classifier fitting took ", total)

    output = np.empty(mask.shape)
    output.fill(-9999)

    pos = 0
    for i in range(mask.shape[0]):
        for j in range(mask.shape[1]):
            if mask[i, j]:
                output[i, j] = predicted[pos]
                pos += 1

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
    with rasterio.open(
        f"{year}.tif",
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

    t_end = time.time()

    total = t_end - t_start
    print(f"{year} took {total}")
