#!/bin/bash

# typical paremeters to execute a single calibration loop on the AAVS2 data (at the moment in debug mode : 

echo "python ~/aavs-calibration/calibration_loop.py --config=/opt/aavs/config/aavs2.yml -i enp216s0f0 -d /data/"
python ~/aavs-calibration/calibration_loop.py --config=/opt/aavs/config/aavs2.yml -i enp216s0f0 -d /data/ 
