#!/bin/bash

RA_deg=0
if [[ -n "$1" && "$1" != "-" ]]; then
   RA_deg=$1
fi

DEC_deg=0
if [[ -n "$2" && "$2" != "-" ]]; then
   DEC_deg=$2
fi

sleep_time=30
if [[ -n "$3" && "$3" != "-" ]]; then
   sleep_time=$3
fi

station_name=eda2
if [[ -n "$4" && "$4" != "-" ]]; then
   station_name=$4
fi

while [ 1 ];
do
   echo "point_station_radec.sh $RA_deg $DEC_deg $station_name"
   point_station_radec.sh $RA_deg $DEC_deg $station_name
   
   echo "sleep $sleep_time"
   sleep $sleep_time
done
