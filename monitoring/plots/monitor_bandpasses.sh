#!/bin/bash

source /opt/aavs/python/bin/activate

echo "python /opt/aavs/bin/monitor_bandpasses.py --interface=enp216s0f0 --config=/opt/aavs/config/eda2.yml --plot_directory=/data/monitoring/integrated_data/eda2/bandpass/"
python /opt/aavs/bin/monitor_bandpasses.py --interface=enp216s0f0 --config=/opt/aavs/config/eda2.yml --plot_directory=/data/monitoring/integrated_data/eda2/bandpass/
