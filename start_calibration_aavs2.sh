#!/bin/bash

# Script which can be put into CRONTAB 

# enviornment
source ~/aavs-calibration/runtime_aavs2.sh

dt=`date +%Y%m%d`

cd /data/real_time_calibration
echo "calibration_loop_aavs2.sh \"--beam_correct\" 1 > ${dt}_calibration.log 2>&1"
calibration_loop_aavs2.sh "--beam_correct" 1 > ${dt}_calibration.log 2>&1

