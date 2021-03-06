#!/usr/bin/python3

# This script converts csv files containing flow/od data as can be obtained from
# ctpp.transportation.org to a format that can be imported into the pct

import glob
import pandas as pd
import numpy  as np
import stplanpy as stp

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

for county in counties:
    print(county)

    file_list = glob.glob("../pct-inputs/01_raw/02_travel_data/commute/taz/" + county + "*.csv")
    for index, file_path in enumerate(file_list):
        print(file_path)
        if index == 0:
            flow_data = stp.read_acs(file_path)
        else:
            temp_data = stp.read_acs(file_path)

            flow_data = pd.concat([flow_data, temp_data])

    flow_data.to_csv("../pct-inputs/02_intermediate/02_travel_data/commute/taz/" + county + "-BayArea_od.csv", index=False)
