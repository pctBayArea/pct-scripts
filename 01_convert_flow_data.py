#!/usr/bin/python3

# This script converts csv files containing flow/od data as can be obtained from
# ctpp.transportation.org to a format that can be imported into the pct

import os
import glob
import pandas as pd
import numpy  as np
import stplanpy as stp

in_dir = os.path.expanduser("../pct-inputs/01_raw/")
out_dir = os.path.expanduser("../pct-inputs/02_intermediate/")

################################################################################

counties = [
    "AlamedaCounty", 
    "ContraCostaCounty", 
    "MarinCounty", 
    "NapaCounty", 
    "SanFranciscoCounty", 
    "SanMateoCounty", 
    "SantaClaraCounty", 
    "SolanoCounty", 
    "SonomaCounty"]

init = True

for county in counties:
    print(county)

    file_list = glob.glob(
        in_dir + "02_travel_data/commute/taz/" + county + "*.csv")
    for i, file_path in enumerate(file_list):
        print(file_path)
        if (init):
            flow_data = stp.read_acs(file_path)

            init = False
        else:
            temp_data = stp.read_acs(file_path)

            flow_data = pd.concat([flow_data, temp_data], ignore_index=True)

# Define some groups    
flow_data["active"] = (
    + flow_data["walk"] 
    + flow_data["bike"])
flow_data["transit"] = (
    + flow_data["bus"] 
    + flow_data["streetcar"] 
    + flow_data["subway"] 
    + flow_data["railroad"] 
    + flow_data["ferry"])
flow_data["carpool"] = (
    + flow_data["car_2p"]
    + flow_data["car_3p"]
    + flow_data["car_4p"]
    + flow_data["car_5p"]
    + flow_data["car_7p"])

# People working from home do not travel    
flow_data["all"] = flow_data["all"] - flow_data["home"]

# Columns to keep
flow_data = flow_data[[
    "orig_taz", 
    "dest_taz", 
    "all", 
    "home", 
    "walk", 
    "bike", 
    "sov", 
    "active", 
    "transit", 
    "carpool"]]

## Add return data for commute trips per day
#fd = flow_data.copy()
#fd = fd[[
#    "dest_taz", 
#    "orig_taz", 
#    "all", 
#    "home", 
#    "walk", 
#    "bike", 
#    "sov", 
#    "active", 
#    "transit", 
#    "carpool"]]
#fd.rename(columns = {
#    "dest_taz":"orig_taz", 
#    "orig_taz":"dest_taz"}, inplace = True)
#flow_data = pd.concat([flow_data, fd], ignore_index=True)

# Fix index
flow_data = flow_data.reset_index(drop=True)

# Write data to disk
flow_data.to_pickle(out_dir + "02_travel_data/commute/flow_data.pkl")

################################################################################
