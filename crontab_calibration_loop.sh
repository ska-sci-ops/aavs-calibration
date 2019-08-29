#!/bin/bash

cal_path=/home/aavs/aavs-calibration/
log_dir=/home/aavs/msok/log/
dtm=`date +%Y%m%d_%H%M%S`

source ${cal_path}/env/calibration_environment 

echo "TEST : MIRBIN = $MIRBIN"
echo "/usr/bin/python ${cal_path}/calibration_loop.py --config=/opt/aavs/config/eda2_full_delayperant.yml -i eth3:1 -d /storage/ >  /home/aavs/msok/log/${dtm}_calibration_loop.log 2>&1"
/usr/bin/python ${cal_path}/calibration_loop.py --config=/opt/aavs/config/eda2_full_delayperant.yml -i eth3:1 -d /storage/ >  /home/aavs/msok/log/${dtm}_calibration_loop.log 2>&1
