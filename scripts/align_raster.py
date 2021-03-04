import argparse
import multiprocessing
import os
import pickle
import subprocess
import sys
from random import randint
from time import sleep

import georasters as gr
import numpy as np
from osgeo import gdal, osr


def save_img(data, geotransform, proj, outPath, noDataValue=np.nan, split=False):
    # Start the gdal driver for GeoTIFF
    if outPath == "MEM":
        driver = gdal.GetDriverByName("MEM")
    else:
        driver = gdal.GetDriverByName("GTiff")

    paths = []
    shape = data.shape
    if len(shape) > 2:
        if split:
            for i in range(shape[2]):
                path = os.path.join(
                    os.path.dirname(outPath),
                    str(i + 1) + "_" + os.path.basename(outPath),
                )
                ds = driver.Create(
                    path,
                    shape[1],
                    shape[0],
                    1,
                    gdal.GDT_Float32,
                    ["COMPRESS=LZW", "NUM_THREADS=ALL_CPUS", "BIGTIFF=YES"],
                )
                ds.SetProjection(proj)
                ds.SetGeoTransform(geotransform)
                ds.GetRasterBand(1).WriteArray(data[:, :, i])
                ds.GetRasterBand(1).SetNoDataValue(noDataValue)
                ds.FlushCache()
                ds = None
                paths.append(path)
        else:
            ds = driver.Create(
                outPath,
                shape[1],
                shape[0],
                shape[2],
                gdal.GDT_Float32,
                ["COMPRESS=LZW", "NUM_THREADS=ALL_CPUS", "BIGTIFF=YES"],
            )
            ds.SetProjection(proj)
            ds.SetGeoTransform(geotransform)
            for i in range(shape[2]):
                ds.GetRasterBand(i + 1).WriteArray(data[:, :, i])
                ds.GetRasterBand(i + 1).SetNoDataValue(noDataValue)
            ds.FlushCache()
            ds = None
            paths.append(outPath)
    else:
        ds = driver.Create(
            outPath,
            shape[1],
            shape[0],
            1,
            gdal.GDT_Float32,
            ["COMPRESS=LZW", "NUM_THREADS=ALL_CPUS", "BIGTIFF=YES"],
        )
        ds.SetProjection(proj)
        ds.SetGeoTransform(geotransform)
        ds.GetRasterBand(1).WriteArray(data)
        ds.GetRasterBand(1).SetNoDataValue(noDataValue)
        ds.FlushCache()
        ds = None
        paths.append(outPath)

    return paths


def get_raster_info(raster_path):
    ret = gdal.Info(raster_path, options="-json")
    num_bands = len(ret["bands"])
    prj = ret["coordinateSystem"]["wkt"]
    geoinformation = ret["geoTransform"]
    try:
        nodata = ret["bands"][0]["noDataValue"]
    except KeyError:
        nodata = -9999

    return prj, geoinformation, nodata, num_bands


def apply_band_to_filepath(path, band_num):
    band_path = os.path.join(
        os.path.dirname(path), str(band_num) + "_" + os.path.basename(path)
    )
    return band_path


def get_band_from_filepath(path):
    num = os.path.basename(path).split("_")[0]
    return num


def get_band_raster(input_raster, split_file, current_band):
    sleep(randint(1, 20))
    split_outPath = apply_band_to_filepath(split_file, current_band)
    subprocess.run(
        [
            "gdal_translate",
            "-b",
            str(current_band),
            "-co",
            "COMPRESS=LZW",
            "-co",
            "NUM_THREADS=ALL_CPUS",
            input_raster,
            split_outPath,
        ]
    )
    print("band {} is split".format(current_band))
    return split_outPath


def warp_raster_func(warped_file, split_file_path, kwargs, dest_prj):
    sleep(randint(1, 20))
    srs = osr.SpatialReference(wkt=dest_prj)
    band_n = get_band_from_filepath(split_file_path)
    warp_outPath = apply_band_to_filepath(warped_file, band_n)
    kwargs["dstSRS"] = srs
    gdal.Warp(warp_outPath, split_file_path, **kwargs)
    print("band {} is warped".format(band_n))
    return warp_outPath


def align_raster_func(path, alignraster, pickle_filename):
    sleep(randint(1, 20))
    band = get_band_from_filepath(path)
    out_filename = apply_band_to_filepath(pickle_filename, band)
    (alignedraster_o, alignedraster_a, GeoT_a) = gr.align_rasters(
        path, alignraster, how=np.mean
    )
    array = np.array(alignedraster_o)
    with open(out_filename, "wb") as f:
        pickle.dump([array, path, GeoT_a], f)
    print("band {} is aligned".format(out_filename))
    return out_filename


def save_raster_func(
    alignraster_prj, dst_filename, alignraster_nodata, pickle_filename
):
    sleep(randint(1, 20))
    with open(pickle_filename, "rb") as f:
        line = pickle.load(f)
    n = get_band_from_filepath(pickle_filename)
    dest_name = apply_band_to_filepath(dst_filename, n)
    save_img(
        line[0],
        list(line[2]),
        alignraster_prj,
        dest_name,
        noDataValue=alignraster_nodata,
        split=False,
    )
    print("band {} is saved".format(dest_name))
    return dest_name


def align_raster_full(alignraster, input_raster, dst_filename, temp_dir):
    # NOTE: rasterband is kept track of with integers before an underscore in the file names

    # this is used for split and warp, it is not used for align or save because of ram limitations
    cpu = multiprocessing.cpu_count() - 1

    # get raster data
    (
        alignraster_prj,
        alignraster_geoinformation,
        alignraster_nodata,
        alignraster_num_bands,
    ) = get_raster_info(alignraster)
    (
        input_raster_prj,
        input_raster_geoinformation,
        input_raster_nodata,
        input_raster_num_bands,
    ) = get_raster_info(input_raster)
    xRes = alignraster_geoinformation[1]
    yRes = alignraster_geoinformation[5]

    # split input raster into bands
    split_file = os.path.join(temp_dir, "split_raster.tif")
    input = [(input_raster, split_file, n + 1) for n in range(input_raster_num_bands)]
    with multiprocessing.Pool(processes=cpu) as p:
        split_file_paths = p.starmap_async(get_band_raster, input).get()
        p.close()
        p.join()
    print("input file is split")
    print(split_file_paths)

    sleep(randint(1, 20))

    # warp each split file
    kwargs = {
        "format": "GTiff",
        "xRes": xRes,
        "yRes": yRes,
        "resampleAlg": "lanczos",
        "srcNodata": input_raster_nodata,
        "dstNodata": alignraster_nodata,
        "creationOptions": ["COMPRESS=LZW", "NUM_THREADS=ALL_CPUS"],
    }
    warped_file = os.path.join(temp_dir, "warped_raster.tif")
    input = [
        (warped_file, split_file_path, kwargs, alignraster_prj)
        for split_file_path in split_file_paths
    ]
    with multiprocessing.Pool(processes=cpu) as p:
        warped_paths = p.starmap_async(warp_raster_func, input).get()
        p.close()
        p.join()
    print("gdal warp has finished")
    print(warped_paths)

    sleep(randint(1, 20))

    # align each warped file
    aligned_file = os.path.join(temp_dir, "aligned_pickle.pkl")
    input = [(warped_path, alignraster, aligned_file) for warped_path in warped_paths]
    with multiprocessing.Pool(processes=3) as p:
        pickle_paths = p.starmap_async(align_raster_func, input).get()
        p.close()
        p.join()
    print("align raster has finished")
    print(pickle_paths)

    sleep(randint(1, 20))

    # save the pkl to raster
    input = [
        (alignraster_prj, dst_filename, alignraster_nodata, pickle_filename)
        for pickle_filename in pickle_paths
    ]
    with multiprocessing.Pool(processes=4) as p:
        result = p.starmap_async(save_raster_func, input).get()
        p.close()
        p.join()
    print("saving rasters has finished")
    print(result)


def get_parser():
    desc = "make the transforms for the icp json in a directory"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--dst_filename", "-d", help="Path to save band rasters")
    parser.add_argument("--raster", "-r", help="Path to input raster")
    parser.add_argument("--alignraster", "-a", help="path to raster to align to")
    parser.add_argument("--temp_dir", "-t", help="directory to use for temp files")
    return parser


def main(rawargs):
    """
    align raster to another raster

    Parameters
    ----------
    dst_filename: str
        Path to save band rasters
    raster: str
        Path to input raster
    alignraster: str
        path to raster to align to
    temp_dir: str
        directory to use for temp files
    Returns
    -------
    None

    Examples
    --------
    python align_raster.py \
    -d "/media/desktop-linux/my_book/testdata/2013_sat.tif" \
    -r "/home/desktop-linux/2013_imagery/clipped_data/clipped_2013_sat.tif" \
    -a "/home/desktop-linux/2013_imagery/clipped_data/clipped_2013_nlcd.tif" \
    -t "/media/desktop-linux/my_book/testdata/working"
    """

    args = get_parser().parse_args(rawargs)

    dst_filename = args.dst_filename

    raster = args.raster
    if not os.path.exists(raster):
        print("Unable to find path to raster: %s" % args.raster)
        sys.exit(1)

    alignraster = args.alignraster
    if not os.path.exists(alignraster):
        print("Unable to find path to alignraster: %s" % args.alignraster)
        sys.exit(1)

    temp_dir = args.temp_dir
    if not os.path.exists(temp_dir):
        print("Unable to find path to temp_dir: %s" % args.temp_dir)
        sys.exit(1)

    align_raster_full(alignraster, raster, dst_filename, temp_dir)


if __name__ == "__main__":
    main(sys.argv[1:])
