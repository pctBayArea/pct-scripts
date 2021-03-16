#!/usr/bin/python3

import os
import glob
import numpy as np
import pandas as pd
import stplanpy as stp

in_dir = os.path.expanduser("../pct-inputs/02_intermediate/")
out_dir = os.path.expanduser("../pct-dash/static/commute/")

################################################################################

if os.path.isfile("flow_data.pkl"):
    print("Read flow_data pickle")
# Read pickle
    flow_data = pd.read_pickle("flow_data.pkl")

# Read taz data
    taz = pd.read_pickle(in_dir + "01_geographies/bayArea_taz.pkl")
else:
    print("Compute flow_data")
# Read flow data
    flow_data = pd.read_pickle(in_dir + "02_travel_data/commute/flow_data.pkl")

# Read taz data
    taz = pd.read_pickle(in_dir + "01_geographies/bayArea_taz.pkl")
    taz_cent = pd.read_pickle(in_dir + "01_geographies/bayArea_taz_cent.pkl")

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

# Compute origin destination lines and distances
    flow_data = stp.od_lines(flow_data, taz_cent)

# Compute go_dutch scenario
    flow_data["go_dutch"] = stp.go_dutch(flow_data)

    flow_data.to_pickle("flow_data.pkl")

stp.plot_dist(flow_data, out_dir)

################################################################################

if os.path.isfile("taz.pkl"):
    print("Read taz pickle")
# Read pickle
    taz = pd.read_pickle("taz.pkl")
else:
    print("Compute taz")
# Add trip data to data frame
    taz["all"]      = 0.0
    taz["sov"]      = 0.0
    taz["bike"]     = 0.0
    taz["go_dutch"] = 0.0

# Total number of commute trips in taz consistst of:
# * trips that start and end in same taz
# * trips that start elsewhere and end in taz
# * trips that start in taz and end elsewhere

    for tazce in taz.iterrows():
        fd = flow_data.loc[(flow_data["orig_taz"] == tazce[0]) | (flow_data["dest_taz"] == tazce[0])]
        if not fd.empty:
            taz.loc[tazce[0], "all"]      = fd["all"].sum()
            taz.loc[tazce[0], "sov"]      = fd["sov"].sum()
            taz.loc[tazce[0], "bike"]     = fd["bike"].sum()
            taz.loc[tazce[0], "go_dutch"] = fd["go_dutch"].sum()

    taz["sov"]      /= taz["all"]
    taz["bike"]     /= taz["all"]
    taz["go_dutch"] /= taz["all"]

    taz["sov"]      = taz["sov"].fillna(0.0)
    taz["bike"]     = taz["bike"].fillna(0.0)
    taz["go_dutch"] = taz["go_dutch"].fillna(0.0)

    taz.to_pickle("taz.pkl")

################################################################################

# Read place data
place = pd.read_pickle(in_dir + "01_geographies/bayArea_place.pkl")

# Add trip data to data frame
place["all"]      = 0.0
place["sov"]      = 0.0
place["bike"]     = 0.0
place["go_dutch"] = 0.0

for placefp in place.iterrows():
    fd = flow_data.loc[(flow_data["orig_plc"] == placefp[0]) | (flow_data["dest_plc"] == placefp[0])]
    if not fd.empty:
        place.loc[placefp[0], "all"]      = fd["all"].sum()
        place.loc[placefp[0], "sov"]      = fd["sov"].sum()
        place.loc[placefp[0], "bike"]     = fd["bike"].sum()
        place.loc[placefp[0], "go_dutch"] = fd["go_dutch"].sum()

place["sov"]      /= place["all"]
place["bike"]     /= place["all"]
place["go_dutch"] /= place["all"]

place["sov"]      = place["sov"].fillna(0.0)
place["bike"]     = place["bike"].fillna(0.0)
place["go_dutch"] = place["go_dutch"].fillna(0.0)

place.to_crs("EPSG:4326").to_file(out_dir + "bayArea_place.GeoJson", driver="GeoJSON")
place.to_pickle(out_dir + "bayArea_place.pkl")

# Organize per place
for placefp in place.iterrows():
    tz = taz.loc[(taz["placefp"] == placefp[0])].copy()
    if not tz.empty:
        name = place.loc[placefp[0], "name"]
        print(name)
# filter out place
        pc = place.loc[place["name"] != name]
        name = name.replace(" ","")
        path = out_dir + "place/" + name 
        if not os.path.isdir(path):
            os.mkdir(path)

        tz["name"] = tz.index

# Remove NaN (countyfp)
        tz = tz[["name", "all", "sov", "bike", "go_dutch", "geometry"]]
        pc = pc[["name", "all", "sov", "bike", "go_dutch", "geometry"]]
        
        tz["geometry"] = tz["geometry"].simplify(2.0)
        pc["geometry"] = pc["geometry"].simplify(20.0)

        tz.to_crs("EPSG:4326").to_file(path + "/taz.GeoJson", driver="GeoJSON")
        pc.to_crs("EPSG:4326").to_file(path + "/place.GeoJson", driver="GeoJSON")

    fd = flow_data.loc[(flow_data["orig_plc"] == placefp[0]) | (flow_data["dest_plc"] == placefp[0])]
    if not fd.empty:
        name = place.loc[placefp[0], "name"]
        name = name.replace(" ","")
        path = out_dir + "place/" + name 
        if not os.path.isdir(path):
            os.mkdir(path)

        stp.plot_dist(fd, path)

        fd = fd[["all", "bike", "go_dutch", "geometry", "distance", "gradient"]]
        fd = fd.loc[fd["distance"] > 0]
        fd = fd.loc[fd["distance"] < 30000]
        fd = fd.nlargest(100, "bike")
        fd.to_crs("EPSG:4326").to_file(path + "/line.GeoJson", driver="GeoJSON")
        fd.to_pickle(path + "/line.pkl")

################################################################################

# Read county data
county = pd.read_pickle(in_dir + "01_geographies/bayArea_county.pkl")

# Add trip data to data frame
county["all"]      = 0.0
county["sov"]      = 0.0
county["bike"]     = 0.0
county["go_dutch"] = 0.0

for countyfp in county.iterrows():
    fd = flow_data.loc[(flow_data["orig_cnt"] == countyfp[0]) | (flow_data["dest_cnt"] == countyfp[0])]
    if not fd.empty:
        county.loc[countyfp[0], "all"]      = fd["all"].sum()
        county.loc[countyfp[0], "sov"]      = fd["sov"].sum()
        county.loc[countyfp[0], "bike"]     = fd["bike"].sum()
        county.loc[countyfp[0], "go_dutch"] = fd["go_dutch"].sum()

county["sov"]      /= county["all"]
county["bike"]     /= county["all"]
county["go_dutch"] /= county["all"]

county["sov"]      = county["sov"].fillna(0.0)
county["bike"]     = county["bike"].fillna(0.0)
county["go_dutch"] = county["go_dutch"].fillna(0.0)

county.to_crs("EPSG:4326").to_file(out_dir + "bayArea_county.GeoJson", driver="GeoJSON")
county.to_pickle(out_dir + "bayArea_county.pkl")

# Organize per county
for countyfp in county.iterrows():
    tz = taz.loc[(taz["countyfp"] == countyfp[0])].copy()
    if not tz.empty:
        name = county.loc[countyfp[0], "name"]
        print(name)
# filter out county
        ct = county.loc[county["name"] != name]
        name = name.replace(" ","")
        path = out_dir + "county/" + name 
        if not os.path.isdir(path):
            os.mkdir(path)
        
        tz["name"] = tz.index

# Remove NaN (placefp)
        tz = tz[["name", "all", "sov", "bike", "go_dutch", "geometry"]]
        ct = ct[["name", "all", "sov", "bike", "go_dutch", "geometry"]]
        
        tz["geometry"] = tz["geometry"].simplify(2.0)
        ct["geometry"] = ct["geometry"].simplify(20.0)

        tz.to_crs("EPSG:4326").to_file(path + "/taz.GeoJson", driver="GeoJSON")
        ct.to_crs("EPSG:4326").to_file(path + "/county.GeoJson", driver="GeoJSON")

    fd = flow_data.loc[(flow_data["orig_cnt"] == countyfp[0]) | (flow_data["dest_cnt"] == countyfp[0])]
    if not fd.empty:
        name = county.loc[countyfp[0], "name"]
        name = name.replace(" ","")
        path = out_dir + "county/" + name 
        if not os.path.isdir(path):
            os.mkdir(path)

        stp.plot_dist(fd, path)

        fd = fd[["all", "bike", "go_dutch", "geometry", "distance", "gradient"]]
        fd = fd.loc[fd["distance"] > 0]
        fd = fd.loc[fd["distance"] < 30000]
        fd = fd.nlargest(100, "bike")
        fd.to_crs("EPSG:4326").to_file(path + "/line.GeoJson", driver="GeoJSON")
        fd.to_pickle(path + "/line.pkl")

################################################################################
