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

object="-"
if [[ -n "$6" && "$6" != "-" ]]; then
   object=$6
fi

options=""
if [[ -n "$7" && "$7" != "-" ]]; then
   options=$7
fi

start_uxtime=-1
if [[ -n "$8" && "$8" != "-" ]]; then
   start_uxtime=$8
fi

echo "#################################################"
echo "PARAMETERS:"
echo "#################################################"
echo "start_uxtime = $start_uxtime"
echo "#################################################"

if [[ $start_uxtime -gt 0 ]]; then
   echo "INFO : start_uxtime = $start_uxtime -> waiting for the start of re-pointing loop until uxtime = $start_uxtime"

   echo "wait_for_unixtime.sh $start_uxtime"
   wait_for_unixtime.sh $start_uxtime
else 
   echo "INFO : no start_uxtime specified -> starting re-pointing loop immediately"
fi

# 2022-11-03 : after both stations use the same firmware --delay_sign=-1 option added as default in point_station_radec.sh
# if [[ $station_name == "aavs2" || $station_name == "AAVS2" ]]; then
#   options="--delay_sign=-1"
# fi

ux=`date +%s`
end_ux=$(($ux + $interval))

while [[  $ux -le $end_ux ]];
do
   echo 
   echo "Unixtime = $ux"
   echo "point_station_radec.sh $RA_deg $DEC_deg $station_name $object \"$options\""
   point_station_radec.sh $RA_deg $DEC_deg $station_name $object "$options"
   
   echo "sleep $sleep_time"
   sleep $sleep_time
   
   ux=`date +%s`
done

echo "Pointing loop finished at :"
date
