#!/bin/bash

options="" # was --skip-db
if [[ -n "$1" && "$1" != "-" ]]; then
   options="$1"
fi

do_init=0
if [[ -n "$2" && "$2" != "-" ]]; then
   do_init=$2
fi


if [[ $do_init -gt 0 ]]; then
   echo "python  /opt/aavs/bin/station.py --config=/opt/aavs/config/eda2.yml -IP"
   python  /opt/aavs/bin/station.py --config=/opt/aavs/config/eda2.yml -IP
   
   # WARNING : second time is required due to some bug in /opt/aavs/bin/station.py related to log files 
   #           which causes issues with the 1st initalisation
   echo "python  /opt/aavs/bin/station.py --config=/opt/aavs/config/eda2.yml -IP"
   python  /opt/aavs/bin/station.py --config=/opt/aavs/config/eda2.yml -IP
else
   echo "WARNING : station initialisation is not required"
fi

# typical paremeters to execute a single calibration loop on the AAVS2 data (at the moment in debug mode : 
echo "python /home/aavs/aavs-calibration/calibration_loop.py --config=/opt/aavs/config/eda2.yml -i enp216s0f0 -d /data/ ${options}"
python /home/aavs/aavs-calibration/calibration_loop.py --config=/opt/aavs/config/eda2.yml -i enp216s0f0 -d /data/ ${options} 

echo "post_calibration_actions.sh EDA2"
post_calibration_actions.sh EDA2 