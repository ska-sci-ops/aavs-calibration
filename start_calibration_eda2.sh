#!/bin/bash

# Script which can be put into CRONTAB 

# environment :
source /opt/aavs/python/bin/activate
export PATH=~/aavs-calibration/:~/aavs-calibration/station:$PATH
source /home/aavs/Software/miriad/miriad/MIRRC.sh
export PATH=${PATH}:${MIRBIN}

dt=`date +%Y%m%d`

cd /data/real_time_calibration
echo "~/aavs-calibration/calibration_loop_eda2.sh \"--beam_correct\" 1  > ${dt}_calibration.log 2>&1"
~/aavs-calibration/calibration_loop_eda2.sh "--beam_correct" 1  > ${dt}_calibration.log 2>&1

