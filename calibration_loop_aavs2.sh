#!/bin/bash

options="" # was --skip-db
if [[ -n "$1" && "$1" != "-" ]]; then
   options="$1"
fi

do_init=0
if [[ -n "$2" && "$2" != "-" ]]; then
   do_init=$2
fi

init_options=""
if [[ -n "$3" && "$3" != "-" ]]; then
   init_options="$3"
fi


if [[ $do_init -gt 0 ]]; then
   echo "python  /opt/aavs/bin/station.py --config=/opt/aavs/config/aavs2.yml -IP ${init_options}"
   python  /opt/aavs/bin/station.py --config=/opt/aavs/config/aavs2.yml -IP ${init_options}

   # WARNING : second time is required due to some bug in /opt/aavs/bin/station.py related to log files 
   #           which causes issues with the 1st initalisation
   echo "python  /opt/aavs/bin/station.py --config=/opt/aavs/config/aavs2.yml -IP ${init_options}"
   python  /opt/aavs/bin/station.py --config=/opt/aavs/config/aavs2.yml -IP ${init_options}
else
   echo "WARNING : station initialisation is not required"
fi


# typical paremeters to execute a single calibration loop on the AAVS2 data (at the moment in debug mode : 
echo "python ~/aavs-calibration/calibration_loop.py --config=/opt/aavs/config/aavs2.yml -i enp216s0f0 -d /data/ ${options}"
python ~/aavs-calibration/calibration_loop.py --config=/opt/aavs/config/aavs2.yml -i enp216s0f0 -d /data/ ${options}

export PATH=~/aavs-calibration/station/:$PATH
echo "~/aavs-calibration/station/fit_all_ant_amplitudes.sh 1 1 1 - 3 _amp > fit.out 2>&1"
~/aavs-calibration/station/fit_all_ant_amplitudes.sh 1 1 1 - 3 _amp > fit.out 2>&1
