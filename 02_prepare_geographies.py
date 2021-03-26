#!/usr/bin/python3

# This script extracts Bay Area county, places, and Traffic Analysis Zone geometries for
# the Bay Area from shapefile data and converts it to the geojson format

import os
import glob
import zipfile
import numpy as np
import pandas as pd
import geopandas as gpd
import stplanpy as stp

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

county = gpd.read_file(tmp_dir + "CA_Counties/CA_Counties_TIGER2016.shp")
county = county.to_crs("EPSG:6933")
county.columns = county.columns.str.lower()

# Filter on county codes
county.set_index("countyfp", inplace=True)
county = county.loc[["001", "013", "041", "055", "075", "081", "085", "095", "097"]]

# Select columns to keep
county = county[["name", "geometry"]]

# Write to disk
county.to_crs("EPSG:4326").to_file(out_dir + "bayArea_county.GeoJson", driver="GeoJSON")
county.to_pickle(out_dir + "bayArea_county.pkl")

# Compute centroids
county_cent = county.copy()
county_cent = county_cent.centroid

# Correct centroid locations
# San Franciscor (ignore Farallon Islands)
county_cent.loc["075"] = stp.corr_cent(-122.44790202662216, 37.75659353337424)

county_cent.to_crs("EPSG:4326").to_file(out_dir + "bayArea_county_cent.GeoJson", driver="GeoJSON")
county_cent.to_pickle(out_dir + "bayArea_county_cent.pkl")

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

place = gpd.read_file(tmp_dir + "tl_2019_06_place.shp")
place = place.to_crs("EPSG:6933")
place.columns = place.columns.str.lower()

# Rename to Mountain View, Martinez
place.loc[(place["placefp"] == "49651"), "name"] = "Mountain View, Martinez"

place.set_index("placefp", inplace=True)
place["countyfp"] = np.nan

# Compute centroids
place_cent = place.copy()
place_cent = place_cent.centroid

# Correct centroid locations
# San Franciscor (ignore Farallon Islands)
place_cent.loc["67000"] = stp.corr_cent(-122.44790202662216, 37.75659353337424)

# iterate over counties and check whether places are within them
for countyfp in county.iterrows():
    mask = place_cent.within(county.loc[[ countyfp[0] ]]["geometry"].values[0])
    place.loc[mask,"countyfp"] = countyfp[0]

# Drop places and centroids without countyfp
mask = place["countyfp"].notna()
place = place.loc[mask]
place_cent = place_cent.loc[mask]

# Select columns to keep
place = place[["name", "countyfp", "geometry"]]

# Write to disk
place.to_crs("EPSG:4326").to_file(out_dir + "bayArea_place.GeoJson", driver="GeoJSON")
place.to_pickle(out_dir + "bayArea_place.pkl")

place_cent.to_crs("EPSG:4326").to_file(out_dir + "bayArea_place_cent.GeoJson", driver="GeoJSON")
place_cent.to_pickle(out_dir + "bayArea_place_cent.pkl")

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

taz = gpd.read_file(tmp_dir + "tl_2011_06_taz10.shp")
taz = taz.to_crs("EPSG:6933")
taz.columns = taz.columns.str.lower()
taz["placefp"] = np.nan
taz["area"] = np.nan

# Rename columns for consistency
taz.rename(columns = {"countyfp10":"countyfp", "tazce10":"tazce"}, inplace = True) 

# Filter on county codes
taz.set_index("countyfp", inplace=True, drop=False)
taz = taz.loc[["001", "013", "041", "055", "075", "081", "085", "095", "097"]]
taz.set_index("tazce", inplace=True)

# Compute centroids
taz_cent = taz.copy()
taz_cent = taz_cent.to_crs("EPSG:6933")
taz_cent = taz.centroid

# Correct centroid locations
# Google plex
taz_cent.loc["00101155"] = stp.corr_cent(-122.07805259936053, 37.42332894065777)
# Stanford research park
taz_cent.loc["00100480"] = stp.corr_cent(-122.14512495139151, 37.407136806684605)
# Facebook
taz_cent.loc["00102130"] = stp.corr_cent(-122.1487037864525, 37.48492337393505)
# Alviso
taz_cent.loc["00101013"] = stp.corr_cent(-121.96984835449749, 37.42903692638468)
# Newark
taz_cent.loc["00103259"] = stp.corr_cent(-122.04629989984038, 37.52303561234163)

# Define empty datafame
intersect = pd.DataFrame()

# iterate over counties and check whether places are within them
for i, placefp in place.iterrows():

    print(place.loc[i,"name"])

# Compute distance to TAZ centroid
    taz_dist = taz_cent.distance(place_cent.loc[i])

    for j, tazfp in taz.iterrows():
# Farallon Islands
        if (j == "00104467"):
            taz.loc[j,"placefp"] = "67000"

# Only consider TAZs with centroid within 25km
        if (taz_dist.loc[j] < 25000):
            df_plc = place.loc[place.index == i]
            df_taz = taz.loc[taz.index == j]
            
            df_int = stp.intersect(df_plc, df_taz)
            df_int["tazce"] = j

            if not (df_int.empty):
                area = df_int["geometry"].values[0].area/df_taz["geometry"].values[0].area
# These geometries are near identical suggesting that the TAZ is completely within the place
                if (area > 0.9999):
                    taz.loc[j,"placefp"] = i
                    taz.loc[j,"area"] = 1.0
# Ignore geometries that are too small
                elif (area > 0.001):
                    df_int.loc[0,"placefp"] = i
                    df_int.loc[0,"area"] = area
                    df_int.rename(columns = {"countyfp_1":"countyfp"}, inplace = True)
                    df_int.loc[0,"countyfp"] = np.nan
                    df_int = df_int[["tazce", "countyfp", "placefp", "geometry", "area"]]
                    df_int.set_index("tazce", inplace=True)

                    if (intersect.empty):
                        intersect = df_int
                    else:
                        intersect = pd.concat([intersect, df_int])

# Select columns to keep
taz = taz[["countyfp", "placefp", "geometry", "area"]]

# Append data of partial 
taz = pd.concat([taz, intersect])

# Write to disk
taz.to_crs("EPSG:4326").to_file(out_dir + "bayArea_taz.GeoJson", driver="GeoJSON")
taz.to_pickle(out_dir + "bayArea_taz.pkl")

taz_cent.to_crs("EPSG:4326").to_file(out_dir + "bayArea_taz_cent.GeoJson", driver="GeoJSON")
taz_cent.to_pickle(out_dir + "bayArea_taz_cent.pkl")

# Clean up files
fileList = glob.glob(tmp_dir + "tl_2011_06_taz10.*")
for filePath in fileList:
    try:
        os.remove(filePath)
    except OSError:
        print("Error while deleting file")

################################################################################
