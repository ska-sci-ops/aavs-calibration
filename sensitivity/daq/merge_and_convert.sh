#!/bin/bash

template="20??????_??????"
if [[ -n "$1" && "$1" != "-" ]]; then
   template="$1"
fi

pwd

for subdir in `ls -d ${template}`
do
   cd $subdir
   pwd
  
   # merge :
   # -H disables dumping of .bin files 
   # -i 0.2831 is integration time in seconds when --channel_samples=262144  samples (1.08 usec each) are collected 
   merge_path=`which hdf5_to_uvfits_all.sh`
   echo "bash $merge_path -i 0.2831 -n 8140 -d merged/ -H -S 0 > merge.out"
   bash $merge_path -i 0.2831 -n 8140 -d merged/ -H -S 0 > merge.out 
   
   # move to separate sub-channel dirs :
   cd merged/
   pwd
   echo "~/aavs-calibration/sensitivity/daq/mvch.sh"
   ~/aavs-calibration/sensitivity/daq/mvch.sh      
         
   echo "~/aavs-calibration/sensitivity/daq/convert.sh > conversion.out 2>&1"
   ~/aavs-calibration/sensitivity/daq/convert.sh > conversion.out 2>&1
   cd ../
      

   cd ..
done
