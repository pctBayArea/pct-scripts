#!/usr/bin/python3

# This script extracts Bay Area county, places, and Traffic Analysis Zone geometries for
# the Bay Area from shapefile data and converts it to the geojson format

import os
import glob
import zipfile
import geopandas
import numpy as np
from shapely.geometry import Polygon

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

inDir  = os.path.expanduser('../pct-inputs/01_raw/01_geographies/')
tmpDir = os.path.expanduser('../pct-inputs/02_intermediate/x_temporary_files/unzip/')
outDir = os.path.expanduser('../pct-inputs/02_intermediate/01_geographies/')

################################################################################

# Boundingbox removes Farallon Islands and puts centroid in the city of San Francisco
boundingBox = Polygon([(1754027,651503), (1787460,651726), (1792428,624573), (1759497,624405), (1754027,651503)])
boundingBox = geopandas.GeoDataFrame(geometry=[boundingBox], crs='EPSG:2768')
boundingBox = boundingBox.to_crs('EPSG:3857')

################################################################################

# Extract to temporal location
with zipfile.ZipFile(inDir + 'county_boundaries/ca-county-boundaries.zip', 'r') as zip_ref:
    zip_ref.extractall(tmpDir)

county = geopandas.read_file(tmpDir + 'CA_Counties/CA_Counties_TIGER2016.shp')
county = county.to_crs('EPSG:3857')

# Filter on county codes
county.set_index('COUNTYFP', inplace=True)
county = county.loc[['001', '013', '041', '055', '075', '081', '085', '095', '097']]

# Select columns to keep
county = county[['NAME', 'geometry']]

# Write to disk
county.to_file(outDir + 'bayArea_county.GeoJson', driver='GeoJSON')
county.to_pickle(outDir + 'bayArea_county.pkl')

# Compute centroids
county_cent = county.copy()
county_cent = geopandas.overlay(county_cent, boundingBox, how='difference')
county_cent = county_cent.centroid
county_cent.to_file(outDir + 'bayArea_county_cent.GeoJson', driver='GeoJSON')
county_cent.to_pickle(outDir + 'bayArea_county_cent.pkl')

# Clean up files
fileList = glob.glob(tmpDir + "CA_Counties/*")
for filePath in fileList:
    try:
        os.remove(filePath)
    except OSError:
        print("Error while deleting file")

os.rmdir(tmpDir + "CA_Counties")

################################################################################

# Extract to temporal location
with zipfile.ZipFile(inDir + 'place_boundaries/tl_2019_06_place.zip', 'r') as zip_ref:
    zip_ref.extractall(tmpDir)

place = geopandas.read_file(tmpDir + 'tl_2019_06_place.shp')
place = place.to_crs('EPSG:3857')
place.set_index('PLACEFP', inplace=True)
place['COUNTYFP'] = np.nan

# Compute centroids
place_cent = place.copy()
place_cent = geopandas.overlay(place_cent, boundingBox, how='difference')
place_cent = place_cent.centroid

# iterate over counties and check whether places are within them
for countyfp in county.iterrows():
    mask = place_cent.within(county.loc[[ countyfp[0] ]]['geometry'].values[0])
    place.loc[mask,'COUNTYFP'] = countyfp[0]


# Drop places and centroids without countyfp
mask = place['COUNTYFP'].notna()
place    = place.loc[mask]
place_cent = place_cent.loc[mask]

# Select columns to keep
place = place[['NAME', 'COUNTYFP', 'geometry']]

# Write to disk
place.to_file(outDir + 'bayArea_place.GeoJson', driver='GeoJSON')
place.to_pickle(outDir + 'bayArea_place.pkl')

place_cent.to_file(outDir + 'bayArea_place_cent.GeoJson', driver='GeoJSON')
place_cent.to_pickle(outDir + 'bayArea_place_cent.pkl')

# Clean up files
fileList = glob.glob(tmpDir + 'tl_2019_06_place.*')
for filePath in fileList:
    try:
        os.remove(filePath)
    except OSError:
        print('Error while deleting file')

################################################################################

# Extract to temporal location
with zipfile.ZipFile(inDir + 'taz_boundaries/tl_2011_06_taz10.zip', 'r') as zip_ref:
    zip_ref.extractall(tmpDir)

taz = geopandas.read_file(tmpDir + 'tl_2011_06_taz10.shp')
taz = taz.to_crs('EPSG:3857')
taz['PLACEFP'] = np.nan

# Rename columns for consistency
taz.rename(columns = {'COUNTYFP10':'COUNTYFP', 'TAZCE10':'TAZCE'}, inplace = True) 

# Filter on county codes
taz.set_index('COUNTYFP', inplace=True, drop=False)
taz = taz.loc[['001', '013', '041', '055', '075', '081', '085', '095', '097']]
taz.set_index('TAZCE', inplace=True)

# Compute centroids
taz_cent = taz.copy()
taz_cent = taz_cent.to_crs('EPSG:3857')
taz_cent = taz.centroid

# iterate over counties and check whether places are within them
for placefp in place.iterrows():
    mask = taz_cent.within(place.loc[[ placefp[0] ]]['geometry'].values[0])
    taz.loc[mask,'PLACEFP'] = placefp[0]

# Select columns to keep
taz = taz[['COUNTYFP', 'PLACEFP', 'geometry']]

# Write to disk
taz.to_file(outDir + 'bayArea_taz.GeoJson', driver='GeoJSON')
taz.to_pickle(outDir + 'bayArea_taz.pkl')

taz_cent.to_file(outDir + 'bayArea_taz_cent.GeoJson', driver='GeoJSON')
taz_cent.to_pickle(outDir + 'bayArea_taz_cent.pkl')

# Clean up files
fileList = glob.glob(tmpDir + "tl_2011_06_taz10.*")
for filePath in fileList:
    try:
        os.remove(filePath)
    except OSError:
        print('Error while deleting file')

################################################################################
