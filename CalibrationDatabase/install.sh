#!/bin/bash

echo Installing aavs-calibration database
sudo apt update
yes yes | sudo apt install mongodb
yes yes | sudo apt-get install python-setuptools
sudo python setup.py install
python -m unittest discover