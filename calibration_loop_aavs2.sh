#!/bin/bash

options="" # was --skip-db
if [[ -n "$1" && "$1" != "-" ]]; then
   options="$1"
fi

# typical paremeters to execute a single calibration loop on the AAVS2 data (at the moment in debug mode : 

echo "python ~/aavs-calibration/calibration_loop.py --config=/opt/aavs/config/aavs2.yml -i enp216s0f0 -d /data/ ${options}"
python ~/aavs-calibration/calibration_loop.py --config=/opt/aavs/config/aavs2.yml -i enp216s0f0 -d /data/ ${options}
