#!/bin/bash

AZIM_deg=0
if [[ -n "$1" && "$1" != "-" ]]; then
   AZIM_deg=$1
fi

ELEV_deg=0
if [[ -n "$2" && "$2" != "-" ]]; then
   ELEV_deg=$2
fi

station_name=eda2
if [[ -n "$3" && "$3" != "-" ]]; then
   station_name=$3
fi
station_name_lower=`echo $station_name | awk '{print tolower($1);}'`

antfile=~/aavs-calibration/config/${station_name_lower}/antenna_locations.txt
config_file=/opt/aavs/config/${station_name_lower}.yml

cd ~/aavs-calibration/station/pointing
date
echo "python ./point_station_newsoft.py --static --azimuth=$AZIM_deg --altitude=$ELEV_deg --antenna_locations=${antfile} --config=${config_file}"
python ./point_station_newsoft.py --static --azimuth=$AZIM_deg --altitude=$ELEV_deg --antenna_locations=${antfile} --config=${config_file}
