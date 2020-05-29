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

object=ZENITH
az=0.00
h=90.00
if [[ -n "$3" && "$3" != "-" ]]; then
   object=$3
fi
# object_radec $object
# echo "DEBUG : $object -> ra,dec = $ra , $dec"

if [[ -n "$4" && "$4" != "-" ]]; then
  az=$4
fi

if [[ -n "$5" && "$5" != "-" ]]; then
  h=$5
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

station_name=eda2

echo "###################################################"
echo "PARAMETERS:"
echo "###################################################"
echo "Object = $object"
echo "(az,h) = ( $az , $h ) [deg]"
echo "freq_channel = $freq_channel"
echo "data_dir     = $data_dir"
echo "interval     = $interval"
echo "start_uxtime = $start_uxtime"
echo "n_iter       = $n_iter"
echo "sleep_time   = $sleep_time"
echo "station      = $station_name"
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
   echo "python /opt/aavs/bin/station.py --config=/opt/aavs/config/eda2.yml -IPB"
   python /opt/aavs/bin/station.py --config=/opt/aavs/config/eda2.yml -IPB
else
  echo "WARNING : station initialisation is not required"
fi   


if [[ $calibrate_station -gt 0 ]]; then
  echo "~/aavs-calibration/station/calibrate_station.sh ${freq_channel} ${station}"
  ~/aavs-calibration/station/calibrate_station.sh ${freq_channel} ${station}
else
  echo "WARNING : station calibration is not required"
fi   

# starting monitoring :
echo "nohup ~/Software/hdf5_correlator/scripts/process_station_beam_loop.sh 204 - - 43000 > power.out 2>&1 &"
nohup ~/Software/hdf5_correlator/scripts/process_station_beam_loop.sh 204 - - 43000 > power.out 2>&1 &

i=0
while [[ $i -lt $n_iter ]];
do
   echo
   echo "------------------------------------------------- i = $i -------------------------------------------------"
   date

   # kill old and start new pointing 
   echo "killall point_station_radec_loop.sh acquire_station_beam point_station_azh.sh daq_receiver.py"
   killall point_station_radec_loop.sh acquire_station_beam point_station_azh.sh daq_receiver.py
   echo "sleep 5"
   sleep 5 

   # start pointing :
   pwd   
   echo "~/aavs-calibration/station/pointing/point_station_azh.sh ${az} ${h} ${station_name}"
   ~/aavs-calibration/station/pointing/point_station_azh.sh ${az} ${h} ${station_name}
   pwd
   ps

   # interval
   # WAS :
   # echo "python /opt/aavs/bin/daq_receiver.py -i enp216s0f0 -t 16  -d . -S --channel_samples=262144 --beam_channels=8 --station_samples=1048576 --acquisition_duration=${interval}"
   # python /opt/aavs/bin/daq_receiver.py -i enp216s0f0 -t 16  -d . -S --channel_samples=262144 --beam_channels=8 --station_samples=1048576 --acquisition_duration=${interval}
   
   echo "/opt/aavs/bin/acquire_station_beam -d ./ -t ${interval} -s 1048576 -c 4  -i enp216s0f0 -p 10.0.10.190"
   /opt/aavs/bin/acquire_station_beam -d ./ -t ${interval} -s 1048576 -c 4  -i enp216s0f0 -p 10.0.10.190 
   
   i=$(($i+1))
   
   if [[ $i -lt $n_iter ]]; then
      echo "i= $i < $n_iter -> sleep $sleep_time"
      sleep $sleep_time
   else
      echo "Iterations finished i = $i ( >= $n_iter ) at :"
      date
   fi
done

