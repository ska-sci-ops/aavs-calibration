#!/bin/bash

cd /data/monitoring/integrated_data/eda2

killall clean.sh

echo "nohup ~/bin/clean.sh > clean.out 2>&1 &"
nohup ~/bin/clean.sh > clean.out 2>&1 &

echo "python /opt/aavs/bin/aavs_extra_monitor.py --config=/opt/aavs/config/eda2.yml  --directory=/data/monitoring/integrated_data/eda2 --interface=eno1"
python /opt/aavs/bin/aavs_extra_monitor.py --config=/opt/aavs/config/eda2.yml  --directory=/data/monitoring/integrated_data/eda2 --interface=eno1
