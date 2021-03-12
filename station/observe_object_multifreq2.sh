#!/bin/bash

station=aavs2
if [[ -n "$1" && "$1" != "-" ]]; then
   station=$1
fi

object=J0835-4510
if [[ -n "$2" && "$2" != "-" ]]; then
   object=$2
fi

ra=128.8360
if [[ -n "$3" && "$3" != "-" ]]; then
  ra=$3
fi

dec=-45.1760
if [[ -n "$4" && "$4" != "-" ]]; then
  dec=$4
fi

interval=900
if [[ -n "$5" && "$5" != "-" ]]; then
   interval=$5
fi

dt=`date +%Y%m%d`
data_dir=/data/chris_lee/${dt}/${object}/
if [[ -n "$6" && "$6" != "-" ]]; then
   data_dir=$6
fi

start_uxtime=-1
if [[ -n "$7" && "$7" != "-" ]]; then
   start_uxtime=$7
fi

echo "###################################################"
echo "PARAMETERS:"
echo "###################################################"
echo "station  = $station"
echo "object   = $object"
echo "ra       = $ra"
echo "dec      = $dec"
echo "interval = $interval"
echo "dt       = $dt"
echo "start_uxtime = $start_uxtime"
echo "###################################################"


ux=`date +%s`
start_uxtime_int=`echo $start_uxtime | awk '{printf("%d",$1);}'`
if [[ $start_uxtime_int -gt $ux ]]; then
   echo "Start unix time = $start_uxtime ($start_uxtime_int) -> waiting ..."
   which wait_for_unixtime.sh
   echo "wait_for_unixtime.sh $start_uxtime_int"
   wait_for_unixtime.sh $start_uxtime_int
fi


do_init_station=2

# while [[ $ch -le 450 ]]; 
# 17 coarse channels :  255 minutes ~= 4 hours + 15 minutes
# start 2 hours before transit is good 
for ch in `echo "90 110 130 150 170 190 204 230 250 270 290 310 330 350 370 390 410"`
do
   echo "observe_object.sh $ch ${data_dir}/${ch} ${object} $ra $dec $interval - 1 - - - $station $do_init_station"
   observe_object.sh $ch ${data_dir}/${ch} ${object} $ra $dec $interval - 1 - - - $station $do_init_station

   do_init_station=0   
done
   