#!/bin/bash

export PATH=~/aavs-calibration/station/pointing:$PATH

object_radec()
{
   object=$1
   
   ret=""
   if [[ $object == "B0950" || $object == "J0950" ]]; then
      ra=148.28879042
      dec=7.92659722
   fi 
   
   if [[ $object == "VELA" || $object == "J0835" || $object == "0835" ]]; then
      ra=128.83583333
      dec=-45.17633333
   fi

   if [[ $object == "J1752" || $object == "1752" ]]; then
      ra=268.1475
      dec=23.99672222
   fi
}


freq_channel=204
if [[ -n "$1" && "$1" != "-" ]]; then
   freq_channel=$1
fi

dir=`date +%Y_%m_%d_$object`
data_dir=/data/${data_dir}
if [[ -n "$2" && "$2" != "-" ]]; then
   data_dir=$2
fi

object=J0437
ra=69.3166
dec=-47.2525
if [[ -n "$3" && "$3" != "-" ]]; then
   object=$3
fi
object_radec $object
echo "DEBUG : $object -> ra,dec = $ra , $dec"

if [[ -n "$4" && "$4" != "-" ]]; then
  ra=$4
fi

if [[ -n "$5" && "$5" != "-" ]]; then
  dec=$5
fi

interval=1800
if [[ -n "$6" && "$6" != "-" ]]; then
   interval=$6
fi

start_uxtime=-1
if [[ -n "$7" && "$7" != "-" ]]; then
   start_uxtime=$7
fi

n_iter=1
if [[ -n "$8" && "$8" != "-" ]]; then
   n_iter=$8
fi

sleep_time=1800
if [[ -n "$9" && "$9" != "-" ]]; then
   sleep_time=$9
fi

pointing_interval=${interval}
if [[ -n "${10}" && "${10}" != "-" ]]; then
   pointing_interval=${10}
fi

repointing_resolution=30
if [[ -n "${11}" && "${11}" != "-" ]]; then
   repointing_resolution=${11}
fi

station=eda2
if [[ -n "${12}" && "${12}" != "-" ]]; then
   station=${12}
fi


echo "###################################################"
echo "PARAMETERS:"
echo "###################################################"
echo "station = $station"
echo "Object = $object"
echo "(ra,dec) = ( $ra , $dec ) [deg]"
echo "freq_channel = $freq_channel"
echo "data_dir     = $data_dir"
echo "interval     = $interval"
echo "pointing_interval = $pointing_interval"
echo "start_uxtime = $start_uxtime"
echo "n_iter       = $n_iter"
echo "sleep_time   = $sleep_time"
echo "repointing_resolution = $repointing_resolution"
echo "###################################################"

ux=`date +%s`
if [[ $start_uxtime -gt $ux ]]; then
   echo "Start unix time = $start_uxtime -> waiting ..."
   which wait_for_unixtime.sh
   echo "wait_for_unixtime.sh $start_uxtime"
   wait_for_unixtime.sh $start_uxtime
fi

do_init_station=0
calibrate_station=1

mkdir -p ${data_dir}
cd ${data_dir}

if [[ $do_init_station -gt 0 ]]; then
   echo "Initialising the station"

   # do initialisation :
   echo "python /opt/aavs/bin/station.py --config=/opt/aavs/config/${station}.yml -IPB"
   python /opt/aavs/bin/station.py --config=/opt/aavs/config/${station}.yml -IPB
else
  echo "WARNING : station initialisation is not required"
fi   


if [[ $calibrate_station -gt 0 ]]; then
  echo "~/aavs-calibration/station/calibrate_station.sh ${freq_channel} ${station}"
  ~/aavs-calibration/station/calibrate_station.sh ${freq_channel} ${station}
else
  echo "WARNING : station calibration is not required"
fi   

i=0
while [[ $i -lt $n_iter ]];
do
   echo
   echo "------------------------------------------------- i = $i -------------------------------------------------"
   date

   # kill old and start new pointing 
   echo "killall point_station_radec_loop.sh acquire_station_beam"
   killall point_station_radec_loop.sh acquire_station_beam 
   echo "sleep 5"
   sleep 5 

   # start pointing :
   pwd   
   echo "nohup ~/aavs-calibration/station/pointing/point_station_radec_loop.sh ${ra} ${dec} ${pointing_interval} ${repointing_resolution} ${station} >> pointing.out 2>&1 &"
   nohup ~/aavs-calibration/station/pointing/point_station_radec_loop.sh ${ra} ${dec} ${pointing_interval} ${repointing_resolution} ${station} >> pointing.out 2>&1 &
   pwd
   ps

   # waiting for pointing to start - not to collect data earlier !
   echo "sleep 30"
   sleep 30

   # start acuisition :
   echo "/home/aavs/Software/aavs-system/src/build_new/acquire_station_beam -d ./ -t ${interval} -s 1048576 -c 4  -i enp216s0f0 -p 10.0.10.190 >> daq.out 2>&1"
   /home/aavs/Software/aavs-system/src/build_new/acquire_station_beam -d ./ -t ${interval} -s 1048576 -c 4  -i enp216s0f0 -p 10.0.10.190 >> daq.out 2>&1
   
   # temporary due to the fact that that the program acquire_station_beam ends up with .dat files without group read permission:
   echo "chmod +r *.dat"
   chmod +r *.dat
   
   i=$(($i+1))
   
   if [[ $i -lt $n_iter ]]; then
      echo "i= $i < $n_iter -> sleep $sleep_time"
      sleep $sleep_time
   else
      echo "Iterations finished i = $i ( >= $n_iter ) at :"
      date
   fi
done

