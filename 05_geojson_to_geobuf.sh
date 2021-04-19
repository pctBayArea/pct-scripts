#!/bin/bash

# use geobuf to convert GeoJson files to pbf files for faster loading

for file_in in `find ../pct-outputs/static -name *GeoJson`;
do 
    echo "$file_in";
    file_out=${file_in/pct-outputs/pct-dash};
    file_out=${file_out%.*};
    json2geobuf "$file_in" > "$file_out.pbf";
done     

for file_in in `find ../pct-outputs/static -name line.pkl`;
do 
    echo "$file_in";
    file_out=${file_in/pct-outputs/pct-dash};
    cp "$file_in" "$file_out";
done     
