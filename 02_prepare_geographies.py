#!/usr/bin/python3

# This script extracts Bay Area county, places, and Traffic Analysis Zone geometries for
# the Bay Area from shapefile data and converts it to the geojson format

import os
import glob
import zipfile
import numpy as np
import pandas as pd
import geopandas as gpd
from stplanpy import geo

# Bay Area county codes
# 06 001 Alameda County
# 06 013 Contra Costa County
# 06 041 Marin County
# 06 055 Napa County
# 06 075 San Francisco County
# 06 081 San Mateo County
# 06 085 Santa Clara County
# 06 095 Solano County
# 06 097 Sonoma County

counties = ["001", "013", "041", "055", "075", "081", "085", "095", "097"]

################################################################################

in_dir  = os.path.expanduser("../pct-inputs/01_raw/01_geographies/")
tmp_dir = os.path.expanduser("../pct-inputs/02_intermediate/x_temporary_files/unzip/")
out_dir = os.path.expanduser("../pct-inputs/02_intermediate/01_geographies/")

os.makedirs(tmp_dir, exist_ok=True)
os.makedirs(out_dir, exist_ok=True)

################################################################################
# Counties in the Bay Area
################################################################################

# Extract to temporal location
with zipfile.ZipFile(in_dir + "county_boundaries/ca-county-boundaries.zip", "r") as zip_ref:
    zip_ref.extractall(tmp_dir)

# Read county data
county = geo.read_shp(tmp_dir + "CA_Counties/CA_Counties_TIGER2016.shp")

# Filter on county codes
county = county[county["countyfp"].isin(counties)]

# Select columns to keep
county = county[["name", "countyfp", "geometry"]]

# Clean up files
fileList = glob.glob(tmp_dir + "CA_Counties/*")
for filePath in fileList:
    try:
        os.remove(filePath)
    except OSError:
        print("Error while deleting file")

os.rmdir(tmp_dir + "CA_Counties")

################################################################################
# Places in the Bay Area
################################################################################

# Extract to temporal location
with zipfile.ZipFile(in_dir + "place_boundaries/tl_2019_06_place.zip", "r") as zip_ref:
    zip_ref.extractall(tmp_dir)

# Read place data
place = geo.read_shp(tmp_dir + "tl_2019_06_place.shp")

# Rename to Mountain View, Martinez
place.loc[(place["placefp"] == "49651"), "name"] = "Mountain View, Martinez"

# Compute which places lay inside which county
place = place.in_county(county)

# Clean up files
fileList = glob.glob(tmp_dir + "tl_2019_06_place.*")
for filePath in fileList:
    try:
        os.remove(filePath)
    except OSError:
        print("Error while deleting file")

################################################################################
# TAZ"s in places
################################################################################

# Extract to temporal location
with zipfile.ZipFile(in_dir + "taz_boundaries/tl_2011_06_taz10.zip", "r") as zip_ref:
    zip_ref.extractall(tmp_dir)

# Read taz data
taz = geo.read_shp(tmp_dir + "tl_2011_06_taz10.shp")
#taz["placefp"] = np.nan
#taz["area"] = np.nan

# Rename columns for consistency
taz.rename(columns = {"countyfp10":"countyfp", "tazce10":"tazce"}, inplace = True) 

# Filter on county codes
taz = taz[taz["countyfp"].isin(counties)]

# Compute centroids
taz_cent = taz.cent()

# Correct centroid locations
# Google plex
taz_cent.corr_cent("00101155", -122.07805259936053, 37.42332894065777)
# Stanford research park
taz_cent.corr_cent("00100480", -122.14512495139151, 37.407136806684605)
# Facebook
taz_cent.corr_cent("00102130", -122.1487037864525, 37.48492337393505)
# Alviso
taz_cent.corr_cent("00101013", -121.96984835449749, 37.42903692638468)
# Newark
taz_cent.corr_cent("00103259", -122.04629989984038, 37.52303561234163)

# Compute which taz lay inside a place and which part
taz = taz.in_place(place)

# Write to disk
county.set_index("countyfp", inplace=True)
county.to_geojson(out_dir + "bayArea_county.GeoJson")
county.to_pickle(out_dir + "bayArea_county.pkl")

# Write to disk
place.set_index("placefp", inplace=True)
place.to_geojson(out_dir + "bayArea_place.GeoJson")
place.to_pickle(out_dir + "bayArea_place.pkl")

# Write to disk
taz.set_index("tazce", inplace=True)
taz.to_geojson(out_dir + "bayArea_taz.GeoJson")
taz.to_pickle(out_dir + "bayArea_taz.pkl")

# Write to disk
taz_cent.set_index("tazce", inplace=True)
taz_cent.to_geojson(out_dir + "bayArea_taz_cent.GeoJson")
taz_cent.to_pickle(out_dir + "bayArea_taz_cent.pkl")

# Clean up files
fileList = glob.glob(tmp_dir + "tl_2011_06_taz10.*")
for filePath in fileList:
    try:
        os.remove(filePath)
    except OSError:
        print("Error while deleting file")

################################################################################
