#!/usr/bin/python3

import os
import glob
import pandas
import numpy as np

inDir = os.path.expanduser('../pct-inputs/02_intermediate/')
outDir = os.path.expanduser('../pct-outputs/commute/')

################################################################################

if os.path.isfile('flowData.pkl'):
    print('Read flowData pickle')
# Read pickle
    flowData = pandas.read_pickle('flowData.pkl')

# Read TAZ data
    taz = pandas.read_pickle(inDir + '01_geographies/bayArea_taz.pkl')
else:
    print('Compute flowData')
# Read flow data
    fileList = glob.glob(inDir + '02_travel_data/commute/taz/*.csv')
    for index, files in enumerate(fileList):
        if index == 0:
            flowData = pandas.read_csv(files, dtype={'orig_code':str, 'dest_code':str})
        else:
            tempData = pandas.read_csv(files, dtype={'orig_code':str, 'dest_code':str})

            flowData = pandas.concat([flowData, tempData], ignore_index=True)

# Organize data
    flowData = flowData[['orig_code', 'dest_code', 'all', 'car.1p', 'bicycle']]
    flowData.rename(columns = {'orig_code':'ORIG_TAZ', 'dest_code':'DEST_TAZ', 'all':'ALL', 'car.1p':'SOV', 'bicycle':'BIKE'}, inplace = True)

# Read TAZ data
    taz = pandas.read_pickle(inDir + '01_geographies/bayArea_taz.pkl')

# Add COUNTY and PLACE codes to data frame
    flowData['ORIG_CNT'] = ''
    flowData['DEST_CNT'] = ''
    flowData['ORIG_PLC'] = ''
    flowData['DEST_PLC'] = ''

# Fill in COUNTY and PLACE data frames
    for fD in flowData.iterrows():
        flowData.loc[fD[0], 'ORIG_CNT'] = taz.loc[flowData.loc[fD[0], 'ORIG_TAZ'], 'COUNTYFP']
        flowData.loc[fD[0], 'DEST_CNT'] = taz.loc[flowData.loc[fD[0], 'DEST_TAZ'], 'COUNTYFP']
        flowData.loc[fD[0], 'ORIG_PLC'] = taz.loc[flowData.loc[fD[0], 'ORIG_TAZ'], 'PLACEFP' ]
        flowData.loc[fD[0], 'DEST_PLC'] = taz.loc[flowData.loc[fD[0], 'DEST_TAZ'], 'PLACEFP' ]

    flowData.to_pickle('flowData.pkl')

################################################################################

if os.path.isfile('taz.pkl'):
    print('Read taz pickle')
# Read pickle
    taz = pandas.read_pickle('taz.pkl')
else:
    print('Compute taz')
# Add trip data to data frame
    taz['ALL']  = 0.0
    taz['SOV']  = 0.0
    taz['BIKE'] = 0.0

# Total number of commute trips in TAZ consistst of:
# * trips that start and end in same TAZ
# * trips that start elsewhere and end in TAZ
# * trips that start in TAZ and end elsewhere

    for tazce in taz.iterrows():
        fD = flowData.loc[(flowData['ORIG_TAZ'] == tazce[0]) | (flowData['DEST_TAZ'] == tazce[0])]
        if not fD.empty:
            taz.loc[tazce[0], 'ALL']  = fD['ALL'].sum()
            taz.loc[tazce[0], 'SOV']  = fD['SOV'].sum()
            taz.loc[tazce[0], 'BIKE'] = fD['BIKE'].sum()

    taz['BIKE'] /= taz['ALL']
    taz['SOV']  /= taz['ALL']

    taz.to_pickle('taz.pkl')

################################################################################

# Read place data
place = pandas.read_pickle(inDir + '01_geographies/bayArea_place.pkl')

# Add trip data to data frame
place['ALL']  = 0.0
place['SOV']  = 0.0
place['BIKE'] = 0.0

for placefp in place.iterrows():
    fD = flowData.loc[(flowData['ORIG_PLC'] == placefp[0]) | (flowData['DEST_PLC'] == placefp[0])]
    if not fD.empty:
        place.loc[placefp[0], 'ALL']  = fD['ALL'].sum()
        place.loc[placefp[0], 'SOV']  = fD['SOV'].sum()
        place.loc[placefp[0], 'BIKE'] = fD['BIKE'].sum()

place['BIKE'] /= place['ALL']
place['SOV']  /= place['ALL']

place.to_file(outDir + 'bayArea_place.GeoJson', driver='GeoJSON')
place.to_pickle(outDir + 'bayArea_place.pkl')

# Organize per place
for placefp in place.iterrows():
    tz = taz.loc[(taz['PLACEFP'] == placefp[0])]
    if not tz.empty:
        name = place.loc[placefp[0], 'NAME']
        print(name)
        name = name.replace(" ","")
        path = outDir + 'place/' + name 
        if not os.path.isdir(path):
            os.mkdir(path)
        
        tz.to_file(path + '/taz.GeoJson', driver='GeoJSON')

################################################################################

# Read county data
county = pandas.read_pickle(inDir + '01_geographies/bayArea_county.pkl')

# Add trip data to data frame
county['ALL']  = 0.0
county['SOV']  = 0.0
county['BIKE'] = 0.0

for countyfp in county.iterrows():
    fD = flowData.loc[(flowData['ORIG_CNT'] == countyfp[0]) | (flowData['DEST_CNT'] == countyfp[0])]
    if not fD.empty:
        county.loc[countyfp[0], 'ALL']  = fD['ALL'].sum()
        county.loc[countyfp[0], 'SOV']  = fD['SOV'].sum()
        county.loc[countyfp[0], 'BIKE'] = fD['BIKE'].sum()

county['BIKE'] /= county['ALL']
county['SOV']  /= county['ALL']

county.to_file(outDir + 'bayArea_county.GeoJson', driver='GeoJSON')
county.to_pickle(outDir + 'bayArea_county.pkl')

# Organize per county
for countyfp in county.iterrows():
    tz = taz.loc[(taz['COUNTYFP'] == countyfp[0])]
    if not tz.empty:
        name = county.loc[countyfp[0], 'NAME']
        print(name)
        name = name.replace(" ","")
        path = outDir + 'county/' + name 
        if not os.path.isdir(path):
            os.mkdir(path)
        
        tz.to_file(path + '/taz.GeoJson', driver='GeoJSON')

################################################################################
