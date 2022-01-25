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
data_dir_local=${data_dir}

start_uxtime=-1
if [[ -n "$7" && "$7" != "-" ]]; then
   start_uxtime=$7
fi

freq_list="90 110 130 150 170 190 204 230 250 270 290 310 330 350 370 390 410"
if [[ -n "$8" && "$8" != "-" ]]; then
   freq_list="$8"
fi

calibration_options=""
if [[ -n "$9" && "$9" != "-" ]]; then
   calibration_options=$9
fi

daq_options=""
n_channels=1
if [[ -n "${10}" && "${10}" != "-" ]]; then
   n_channels=${10}
fi

if [[ -n "${11}" && "${11}" != "-" ]]; then
   daq_options=${11}
fi

wait_beteen_observations=-1
if [[ -n "${12}" && "${12}" != "-" ]]; then
   wait_beteen_observations=${12}
fi

use_config_per_freq=1
if [[ -n "${13}" && "${13}" != "-" ]]; then
   use_config_per_freq=${13}
fi


echo "###################################################"
echo "PARAMETERS:"
echo "###################################################"
echo "station  = $station"
echo "data_dir_local = $data_dir_local (data_dir = $data_dir)"
echo "object   = $object"
echo "ra       = $ra"
echo "dec      = $dec"
echo "interval = $interval"
echo "dt       = $dt"
echo "start_uxtime = $start_uxtime"
echo "freq_list = $freq_list"
echo "calibration_options = $calibration_options"
echo "daq_options = $daq_options"
echo "N channels = $n_channels"
echo "wait_beteen_observations = $wait_beteen_observations"
echo "use_config_per_freq = $use_config_per_freq"
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
for ch in `echo $freq_list`
do   
   echo "DEBUG : observing channel = $ch , data_dir = $data_dir"

   end_channel=-1
   if [[ $n_channels -gt 0 ]]; then
      end_channel=$(($ch+$n_channels))
      daq_options="$daq_options --start_channel 0 --nof_channels ${n_channels}"
   fi

   # subdirectory is the name of the channel, but if already exists prefix _001 , _002 etc will be added:
   subdir=${ch}
   if [[ -d ${data_dir}/${ch} ]]; then
      cnt=`ls -d ${data_dir}/${ch}* | wc -l`
      subdir=`echo $cnt | awk -v ch=${ch} '{printf("%d_%03d\n",ch,$1);}'`
      echo "DEBUG : subdir = $subdir -> ${data_dir}/${subdir}/"
   fi

   pwd
   echo "observe_object.sh $ch ${data_dir}/${subdir}/ ${object} $ra $dec $interval - 1 - - - $station $do_init_station - \"${calibration_options}\" - - $n_channels \"${daq_options}\" $use_config_per_freq"
   observe_object.sh $ch ${data_dir}/${subdir}/ ${object} $ra $dec $interval - 1 - - - $station $do_init_station - "${calibration_options}" - - $n_channels "${daq_options}" $use_config_per_freq
   
   # just to make sure the internally changed variable does not propagate here, which seems to be the case
   data_dir=${data_dir_local}
   
   if [[ $wait_beteen_observations -gt 0 ]]; then
      echo "sleep $wait_beteen_observations"
      sleep $wait_beteen_observations
   fi

   # have to re-initialise every time due to change in observing frequency : 
   # first observation has 2 station initialisation (due to bug), but the next ones can do just one
   do_init_station=1
done
   