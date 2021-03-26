#!/bin/bash

# use geobuf to convert GeoJson files to pbf files for faster loading

for filename in `find ../pct-dash/static -name *GeoJson`;
do 
    echo "$filename";
    json2geobuf "$filename" > "${filename%.*}.pbf";
done     
