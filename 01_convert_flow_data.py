#!/usr/bin/python3

# This script converts csv files containing flow/od data as can be obtained from
# ctpp.transportation.org to a format that can be imported into the pct

import os
import glob
import pandas as pd
import numpy  as np
import stplanpy as stp

################################################################################

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

# Read all acs csv files and merge them into one dataframe
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

# Clean up acs flow data
flow_data = flow_data.clean_acs()

# Write data to disk
flow_data.to_pickle(out_dir + "02_travel_data/commute/flow_data.pkl")

################################################################################
