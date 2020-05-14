#!/bin/bash

RA_deg=0
if [[ -n "$1" && "$1" != "-" ]]; then
   RA_deg=$1
fi

DEC_deg=0
if [[ -n "$2" && "$2" != "-" ]]; then
   DEC_deg=$2
fi

interval=3600 # default 1 hour
if [[ -n "$3" && "$3" != "-" ]]; then
   interval=$3
fi

sleep_time=30
if [[ -n "$4" && "$4" != "-" ]]; then
   sleep_time=$4
fi

station_name=eda2
if [[ -n "$5" && "$5" != "-" ]]; then
   station_name=$5
fi

ux=`date +%s`
end_ux=$(($ux + $interval))

while [[  $ux -le $end_ux ]];
do
   echo 
   echo "Unixtime = $ux"
   echo "point_station_radec.sh $RA_deg $DEC_deg $station_name"
   point_station_radec.sh $RA_deg $DEC_deg $station_name
   
   echo "sleep $sleep_time"
   sleep $sleep_time
   
   ux=`date +%s`
done
