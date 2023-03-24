#!/bin/bash

# Script which can be put into CRONTAB 

export PATH=~/aavs-calibration/:~/aavs-calibration/station:$PATH

dt=`date +%Y%m%d`

cd /data/real_time_calibration
echo "~/aavs-calibration/calibration_loop_eda2.sh \"--beam_correct\" 1  > ${dt}_calibration.log 2>&1"
~/aavs-calibration/calibration_loop_eda2.sh "--beam_correct" 1  > ${dt}_calibration.log 2>&1

