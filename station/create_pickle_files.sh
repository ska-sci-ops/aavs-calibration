#!/bin/bash

# ~/aavs-calibration/station/make_station_pickle_file.sh 410 eda2 last

station_name=eda2
if [[ -n "$1" && "$1" != "-" ]]; then
   station_name=$1
fi

ch=0
while [[ $ch -le 512 ]];
do
   ch_str=`echo $ch | awk '{printf("%03d",$1);}'`

   echo "~/aavs-calibration/station/make_station_pickle_file.sh $ch_str $station_name last"
   ~/aavs-calibration/station/make_station_pickle_file.sh $ch_str $station_name last
   
   ch=$(($ch+1))
done
 