#!/bin/bash

cd /data/monitoring/
mkdir -p /data/monitoring/integrated_data/eda2
mkdir -p /data/monitoring/integrated_data/eda2/bandpass/
mkdir -p /data/monitoring/integrated_data/eda2/imageseda-2/

cd /data/monitoring/integrated_data/eda2/

echo "python /opt/aavs/bin/monitor_bandpasses.py --interface=eno1 --config=/opt/aavs/config/eda2.yml --plot_directory=/data/monitoring/integrated_data/eda2/bandpass"
python /opt/aavs/bin/monitor_bandpasses.py --interface=eno1 --config=/opt/aavs/config/eda2.yml --plot_directory=/data/monitoring/integrated_data/eda2/bandpass


