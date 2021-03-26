#!/usr/bin/python3

# This script computes the the elevation data of all the Traffic Analysis Zones
# (TAZ)

import os
import glob
import zipfile
import pandas as pd
import geopandas as gpd
#import matplotlib.pyplot as plt
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
#from rasterio.plot import show
from rasterstats import point_query

################################################################################

in_dir  = os.path.expanduser("../pct-inputs/01_raw/03_elevation/")
tmp_dir = os.path.expanduser("../pct-inputs/02_intermediate/x_temporary_files/unzip/")
out_dir = os.path.expanduser("../pct-inputs/02_intermediate/")

os.makedirs(tmp_dir, exist_ok=True)
os.makedirs(out_dir, exist_ok=True)

################################################################################

# Extract to temporal location
with zipfile.ZipFile(in_dir + "srtm_12_05.zip", "r") as zip_ref:
    zip_ref.extractall(tmp_dir)

dst_crs = "EPSG:6933"

# Reprojecting the GeoTIFF file
with rasterio.open(tmp_dir+"srtm_12_05.tif") as src:
    transform, width, height = calculate_default_transform(
        src.crs, dst_crs, src.width, src.height, *src.bounds)
    kwargs = src.meta.copy()
    kwargs.update({
        "crs": dst_crs,
        "transform": transform,
        "width": width,
        "height": height
    })

    with rasterio.open(out_dir + "03_elevation/srtm_12_05.wgs84.tif", "w", **kwargs) as dst:
        for i in range(1, src.count + 1):
            reproject(
                source=rasterio.band(src, i),
                destination=rasterio.band(dst, i),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                resampling=Resampling.nearest)

# Read TAZ centroids
taz_cent = pd.read_pickle(out_dir + "01_geographies/bayArea_taz_cent.pkl")

# Compute elevation and create dataframe
points = point_query(taz_cent, out_dir + "03_elevation/srtm_12_05.wgs84.tif")

# Create dataframe and write to pickle
taz_elev = pd.DataFrame(points, columns = ["elevation"], index=taz_cent.index)
taz_elev.to_pickle(out_dir + "03_elevation/bayArea_taz_elev.pkl")

#taz_elev["geometry"] = taz_cent 
#taz_elev = gpd.GeoDataFrame(taz_elev)
#taz_elev = taz_elev.set_crs("EPSG:6933")
#taz_elev.to_crs("EPSG:4326").to_file(out_dir + "bayArea_taz_elev.GeoJson", driver="GeoJSON")

# Clean up files
fileList = glob.glob(tmp_dir + "srtm_12_05.*")
fileList.append("../pct-inputs/02_intermediate/x_temporary_files/unzip/readme.txt")
for filePath in fileList:
    try:
        os.remove(filePath)
    except OSError:
        print("Error while deleting file")

################################################################################
