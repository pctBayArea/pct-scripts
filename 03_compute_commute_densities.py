#!/usr/bin/python3

import os
import glob
import numpy as np
import pandas as pd

inDir = os.path.expanduser("../pct-inputs/02_intermediate/")
outDir = os.path.expanduser("../pct-outputs/commute/")

################################################################################

if os.path.isfile("flow_data.pkl"):
    print("Read flow_data pickle")
# Read pickle
    flow_data = pd.read_pickle("flow_data.pkl")

# Read taz data
    taz = pd.read_pickle(inDir + "01_geographies/bayArea_taz.pkl")
else:
    print("Compute flow_data")
# Read flow data
    file_list = glob.glob(inDir + "02_travel_data/commute/taz/*.csv")
    for index, files in enumerate(file_list):
        if index == 0:
            flow_data = pd.read_csv(files, dtype={"orig_code":str, "dest_code":str})
        else:
            fD       = pd.read_csv(files, dtype={"orig_code":str, "dest_code":str})
            flow_data = pd.concat([flow_data, fD], ignore_index=True)

# Organize data
    flow_data = flow_data[["orig_code", "dest_code", "all", "car_1p", "bicycle"]]
    flow_data.rename(columns = {"orig_code":"orig_taz", "dest_code":"dest_taz", "all":"all", "car_1p":"sov", "bicycle":"bike"}, inplace = True)

# Add return data for commute trips per day
    fD = flow_data.copy()
    fD = fD[["dest_taz", "orig_taz", "all", "sov", "bike"]]
    fD.rename(columns = {"dest_taz":"orig_taz", "orig_taz":"dest_taz"}, inplace = True)
    flow_data = pd.concat([flow_data, fD], ignore_index=True)

# Read taz data
    taz = pd.read_pickle(inDir + "01_geographies/bayArea_taz.pkl")

# Add county and place codes to data frame. This data is used to compute mode
# share in counties and places
    flow_data["orig_cnt"] = ""
    flow_data["dest_cnt"] = ""
    flow_data["orig_plc"] = ""
    flow_data["dest_plc"] = ""

    taz_cnt = taz.dropna(subset=["countyfp"])

    for i, tz in taz_cnt.iterrows():
        cntfp = tz["countyfp"]

        flow_data.loc[(flow_data["orig_taz"] == i), "orig_cnt"] = cntfp
        flow_data.loc[(flow_data["dest_taz"] == i), "dest_cnt"] = cntfp

    taz_plc = taz.dropna(subset=["placefp"])

    for i, tz in taz_plc.iterrows():
# We do not know the distribution of origins or destinations within a TAZ.
# Therefore, add TAZ to place if more than 0.5 of its surface area is within
# this place.
        if (tz['area'] > 0.5):
            plcfp = tz["placefp"]
            
            flow_data.loc[(flow_data["orig_taz"] == i), "orig_plc"] = plcfp
            flow_data.loc[(flow_data["dest_taz"] == i), "dest_plc"] = plcfp

    flow_data.to_pickle("flow_data.pkl")

################################################################################

if os.path.isfile("taz.pkl"):
    print("Read taz pickle")
# Read pickle
    taz = pd.read_pickle("taz.pkl")
else:
    print("Compute taz")
# Add trip data to data frame
    taz["all"]  = 0.0
    taz["sov"]  = 0.0
    taz["bike"] = 0.0

# Total number of commute trips in taz consistst of:
# * trips that start and end in same taz
# * trips that start elsewhere and end in taz
# * trips that start in taz and end elsewhere

    for tazce in taz.iterrows():
        fD = flow_data.loc[(flow_data["orig_taz"] == tazce[0]) | (flow_data["dest_taz"] == tazce[0])]
        if not fD.empty:
            taz.loc[tazce[0], "all"]  = fD["all"].sum()
            taz.loc[tazce[0], "sov"]  = fD["sov"].sum()
            taz.loc[tazce[0], "bike"] = fD["bike"].sum()

    taz["bike"] /= taz["all"]
    taz["sov"]  /= taz["all"]

    taz["bike"] = taz["bike"].fillna(0.0)
    taz["sov"] = taz["sov"].fillna(0.0)

    taz.to_pickle("taz.pkl")

################################################################################

# Read place data
place = pd.read_pickle(inDir + "01_geographies/bayArea_place.pkl")

# Add trip data to data frame
place["all"]  = 0.0
place["sov"]  = 0.0
place["bike"] = 0.0

for placefp in place.iterrows():
    fD = flow_data.loc[(flow_data["orig_plc"] == placefp[0]) | (flow_data["dest_plc"] == placefp[0])]
    if not fD.empty:
        place.loc[placefp[0], "all"]  = fD["all"].sum()
        place.loc[placefp[0], "sov"]  = fD["sov"].sum()
        place.loc[placefp[0], "bike"] = fD["bike"].sum()

place["bike"] /= place["all"]
place["sov"]  /= place["all"]

place["bike"] = place["bike"].fillna(0.0)
place["sov"] = place["sov"].fillna(0.0)

place.to_crs("EPSG:4326").to_file(outDir + "bayArea_place.GeoJson", driver="GeoJSON")
place.to_pickle(outDir + "bayArea_place.pkl")

# Organize per place
for placefp in place.iterrows():
    tz = taz.loc[(taz["placefp"] == placefp[0])].copy()
    if not tz.empty:
        name = place.loc[placefp[0], "name"]
        print(name)
# filter out place
        pc = place.loc[place["name"] != name]
        name = name.replace(" ","")
        path = outDir + "place/" + name 
        if not os.path.isdir(path):
            os.mkdir(path)

        tz["name"] = tz.index

# Remove NaN (countyfp)
        tz = tz[["name", "all", "sov", "bike", "geometry"]]
        pc = pc[["name", "all", "sov", "bike", "geometry"]]
        
        tz["geometry"] = tz["geometry"].simplify(1.0)
        pc["geometry"] = pc["geometry"].simplify(10.0)

        tz.to_crs("EPSG:4326").to_file(path + "/taz.GeoJson", driver="GeoJSON")
        pc.to_crs("EPSG:4326").to_file(path + "/place.GeoJson", driver="GeoJSON")

################################################################################

# Read county data
county = pd.read_pickle(inDir + "01_geographies/bayArea_county.pkl")

# Add trip data to data frame
county["all"]  = 0.0
county["sov"]  = 0.0
county["bike"] = 0.0

for countyfp in county.iterrows():
    fD = flow_data.loc[(flow_data["orig_cnt"] == countyfp[0]) | (flow_data["dest_cnt"] == countyfp[0])]
    if not fD.empty:
        county.loc[countyfp[0], "all"]  = fD["all"].sum()
        county.loc[countyfp[0], "sov"]  = fD["sov"].sum()
        county.loc[countyfp[0], "bike"] = fD["bike"].sum()

county["bike"] /= county["all"]
county["sov"]  /= county["all"]

county["bike"] = county["bike"].fillna(0.0)
county["sov"] = county["sov"].fillna(0.0)

county.to_crs("EPSG:4326").to_file(outDir + "bayArea_county.GeoJson", driver="GeoJSON")
county.to_pickle(outDir + "bayArea_county.pkl")

# Organize per county
for countyfp in county.iterrows():
    tz = taz.loc[(taz["countyfp"] == countyfp[0])].copy()
    if not tz.empty:
        name = county.loc[countyfp[0], "name"]
        print(name)
# filter out county
        ct = county.loc[county["name"] != name]
        name = name.replace(" ","")
        path = outDir + "county/" + name 
        if not os.path.isdir(path):
            os.mkdir(path)
        
        tz["name"] = tz.index

# Remove NaN (placefp)
        tz = tz[["name", "all", "sov", "bike", "geometry"]]
        ct = ct[["name", "all", "sov", "bike", "geometry"]]
        
        tz["geometry"] = tz["geometry"].simplify(1.0)
        ct["geometry"] = ct["geometry"].simplify(10.0)

        tz.to_crs("EPSG:4326").to_file(path + "/taz.GeoJson", driver="GeoJSON")
        ct.to_crs("EPSG:4326").to_file(path + "/county.GeoJson", driver="GeoJSON")

################################################################################
