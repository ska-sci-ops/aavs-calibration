#!/bin/bash

for file in `ls *.hdf5`
do
  echo "python ~/aavs-calibration/sensitivity/daq/getch.py $file --mv"
  python ~/aavs-calibration/sensitivity/daq/getch.py $file --mv   
done
