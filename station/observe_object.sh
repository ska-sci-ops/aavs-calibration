#!/bin/bash

export PATH=~/aavs-calibration/station/pointing:$PATH

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
if [[ -n "$3" && "$3" != "-" ]]; then
   object=$3
fi

ra=69.3166
if [[ -n "$4" && "$4" != "-" ]]; then
  ra=$4
fi

dec=-47.2525
if [[ -n "$5" && "$5" != "-" ]]; then
  dec=$5
fi

echo "###################################################"
echo "PARAMETERS:"
echo "###################################################"
echo "Object = $object"
echo "(ra,dec) = ( $ra , $dec ) [deg]"
echo "freq_channel = $freq_channel"
echo "data_dir     = $data_dir"
echo "###################################################"


do_init_station=0
calibrate_station=1
station=eda2
interval=1800

mkdir -p ${data_dir}
cd ${data_dir}

if [[ $do_init_station -gt 0 ]]; then
   echo "Initialising the station"

   # do initialisation :
   echo "python /opt/aavs/bin/station.py --config=/opt/aavs/config/eda2.yml -IPB"
   # python /opt/aavs/bin/station.py --config=/opt/aavs/config/eda2.yml -IPB
else
  echo "WARNING : station initialisation is not required"
fi   


if [[ $calibrate_station -gt 0 ]]; then
  echo "~/aavs-calibration/station/calibrate_station.sh ${freq_channel} ${station}"
  ~/aavs-calibration/station/calibrate_station.sh ${freq_channel} ${station}
else
  echo "WARNING : station calibration is not required"
fi   

# kill old and start new pointing 
echo "killall point_station_radec_loop.sh"
killall point_station_radec_loop.sh 
sleep 5 

# start pointing :
echo "nohup point_station_radec_loop.sh ${ra} ${dec} ${interval} 30 ${station} >> pointing.out 2>&1 &"
nohup point_station_radec_loop.sh ${ra} ${dec} ${interval} 30 ${station} >> pointing.out 2>&1 &

# start acuisition :
echo "nohup /home/aavs/Software/aavs-system/src/build_new/acquire_station_beam -d ./ -t ${interval} -s 1048576 -c 4  -i enp216s0f0 -p 10.0.10.190 >> daq.out 2>&1 &"
nohup /home/aavs/Software/aavs-system/src/build_new/acquire_station_beam -d ./ -t ${interval} -s 1048576 -c 4  -i enp216s0f0 -p 10.0.10.190 >> daq.out 2>&1 &

