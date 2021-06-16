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
from stplanpy import elev

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

# Reproject elevation data
elev.reproj(tmp_dir+"srtm_12_05.tif", out_dir + "03_elevation/srtm_12_05.wgs85.tif")

# Read TAZ centroids
taz_cent = pd.read_pickle(out_dir + "01_geographies/bayArea_taz_cent.pkl")

# Compute elevation and create dataframe
points = point_query(taz_cent, out_dir + "03_elevation/srtm_12_05.wgs84.tif")

# Create dataframe and write to pickle
taz_elev = pd.DataFrame(points, columns = ["elevation"], index=taz_cent.index)
taz_elev.to_pickle(out_dir + "03_elevation/bayArea_taz_elev.pkl")

# Clean up files
fileList = glob.glob(tmp_dir + "srtm_12_05.*")
fileList.append("../pct-inputs/02_intermediate/x_temporary_files/unzip/readme.txt")
for filePath in fileList:
    try:
        os.remove(filePath)
    except OSError:
        print("Error while deleting file")

################################################################################
