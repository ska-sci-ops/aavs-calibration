#!/bin/bash

# ~/aavs-calibration/station/make_station_pickle_file.sh 410 eda2 last

station_name=eda2
if [[ -n "$1" && "$1" != "-" ]]; then
   station_name=$1
fi
station_name_lowercase=`echo $station_name | awk '{print tolower($1);}'`

options=""
if [[ -n "$2" && "$2" != "-" ]]; then
   options="$2"
fi

ch=0
while [[ $ch -le 512 ]];
do
   ch_str=`echo $ch | awk '{printf("%03d",$1);}'`

   echo "~/aavs-calibration/station/make_station_pickle_file.sh $ch_str $station_name_lowercase last \"$options\""
   ~/aavs-calibration/station/make_station_pickle_file.sh $ch_str $station_name_lowercase last "$options"
   
   ch=$(($ch+1))
done
 