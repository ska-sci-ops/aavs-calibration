#!/bin/bash

# Script which can be put into CRONTAB 

# enviornment
source /opt/aavs/python38/python/bin/activate
export PATH=~/aavs-calibration/:~/aavs-calibration/station:$PATH
PGHOST=10.0.10.200
source /home/aavs/Software/miriad/miriad/MIRRC.sh
export PATH=${PATH}:${MIRBIN}

dt=`date +%Y%m%d`

cd /data/real_time_calibration
echo "calibration_loop_aavs2.sh \"--beam_correct\" 1 > ${dt}_calibration.log 2>&1"
calibration_loop_aavs2.sh "--beam_correct" 1 > ${dt}_calibration.log 2>&1

