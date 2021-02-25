#!/usr/bin/python3

# This script extracts Bay Area county, places, and Traffic Analysis Zone geometries for
# the Bay Area from shapefile data and converts it to the geojson format

import os
import glob
import zipfile
import geopandas
import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon, MultiPolygon, GeometryCollection

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
# Counties in the Bay Area
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
county.to_crs('EPSG:4326').to_file(outDir + 'bayArea_county.GeoJson', driver='GeoJSON')
county.to_pickle(outDir + 'bayArea_county.pkl')

# Compute centroids
county_cent = county.copy()
county_cent = geopandas.overlay(county_cent, boundingBox, how='difference')
county_cent = county_cent.centroid
county_cent.to_crs('EPSG:4326').to_file(outDir + 'bayArea_county_cent.GeoJson', driver='GeoJSON')
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
# Places in the Bay Area
################################################################################

# Extract to temporal location
with zipfile.ZipFile(inDir + 'place_boundaries/tl_2019_06_place.zip', 'r') as zip_ref:
    zip_ref.extractall(tmpDir)

place = geopandas.read_file(tmpDir + 'tl_2019_06_place.shp')
place = place.to_crs('EPSG:3857')

# Rename to Mountain View, Martinez
place.loc[(place['PLACEFP'] == "49651"), 'NAME'] = "Mountain View, Martinez"

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
place.to_crs('EPSG:4326').to_file(outDir + 'bayArea_place.GeoJson', driver='GeoJSON')
place.to_pickle(outDir + 'bayArea_place.pkl')

place_cent.to_crs('EPSG:4326').to_file(outDir + 'bayArea_place_cent.GeoJson', driver='GeoJSON')
place_cent.to_pickle(outDir + 'bayArea_place_cent.pkl')

# Clean up files
fileList = glob.glob(tmpDir + 'tl_2019_06_place.*')
for filePath in fileList:
    try:
        os.remove(filePath)
    except OSError:
        print('Error while deleting file')

################################################################################
# TAZ's in places
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

# Define empty datafame
intersect = pd.DataFrame()

# iterate over counties and check whether places are within them
for i, placefp in place.iterrows():

    print(place.loc[i,'NAME'])

# Compute distance to TAZ centroid
    taz_dist = taz_cent.distance(place_cent.loc[i])

    for j, tazfp in taz.iterrows():
# Farallon Islands
        if (j == '00104467'):
            taz.loc[j,'PLACEFP'] = '67000'

# Only consider TAZs with centroid within 25km
        if (taz_dist.loc[j] < 25000):
            plc_df = place.loc[place.index == i]
            taz_df = taz.loc[taz.index == j]
            intersection = geopandas.overlay(plc_df, taz_df, how='intersection', keep_geom_type=False)
            intersection['TAZCE'] = j

            if not (intersection.empty):
                gtype = intersection.geom_type.values[0]
                if (gtype == 'Polygon' or gtype == 'MultiPolygon' or gtype == 'GeometryCollection'):
# These geometries are near identical suggesting that the TAZ is completely within the place
                    area = intersection['geometry'].values[0].area
                    areaRatio =  area / taz_df['geometry'].values[0].area
                    if (areaRatio > 0.9999):
                        taz.loc[j,'PLACEFP'] = i
                    else:
#                    elif (areaRatio > 0.001):
#                    elif (area > 100.0):
                        intersection.loc[0,'PLACEFP'] = i
                        intersection.rename(columns = {'COUNTYFP_1':'COUNTYFP'}, inplace = True)
                        intersection.loc[0,'COUNTYFP'] = np.nan
                        intersection = intersection[['TAZCE', 'COUNTYFP', 'PLACEFP', 'geometry']]
                        intersection.set_index('TAZCE', inplace=True)
                        
                        if (intersection.geom_type.values[0] == "GeometryCollection"):
                            geoms = []
                            for geom in intersection['geometry'].values[0]:
                                gtype = geom.geom_type
                                if (gtype == 'Polygon' or gtype == 'MultiPolygon'):
                                    geoms.append(geom)

                            if (geoms):
                                if (len(geoms) == 1):
                                    geoms = geoms[0]
                                else:
                                    geoms = MultiPolygon(geoms)

                                intersection['geometry'] = geoms

# Only keep areas larger than area_min
                        geoms = []
                        area_min = 100
                        if (intersection.geom_type.values[0] == 'Polygon'):
                            if (intersection['geometry'].values[0].area > area_min):
                                geoms.append(intersection['geometry'].values[0])
                        else:
                            for geom in intersection['geometry'].values[0]:
                                if (geom.area > area_min):
                                    geoms.append(geom)
                            
                        if (geoms):
                            if (len(geoms) == 1):
                                geoms = geoms[0]
                            else:
                                geoms = MultiPolygon(geoms)

                            intersection['geometry'] = geoms

                            if (intersect.empty):
                                intersect = intersection
                            else:
                                intersect = pd.concat([intersect, intersection])

# Select columns to keep
taz = taz[['COUNTYFP', 'PLACEFP', 'geometry']]

# Append data of partial 
taz = pd.concat([taz, intersect])

# Write to disk
taz.to_crs('EPSG:4326').to_file(outDir + 'bayArea_taz.GeoJson', driver='GeoJSON')
taz.to_pickle(outDir + 'bayArea_taz.pkl')

taz_cent.to_crs('EPSG:4326').to_file(outDir + 'bayArea_taz_cent.GeoJson', driver='GeoJSON')
taz_cent.to_pickle(outDir + 'bayArea_taz_cent.pkl')

# Clean up files
fileList = glob.glob(tmpDir + "tl_2011_06_taz10.*")
for filePath in fileList:
    try:
        os.remove(filePath)
    except OSError:
        print('Error while deleting file')

################################################################################
