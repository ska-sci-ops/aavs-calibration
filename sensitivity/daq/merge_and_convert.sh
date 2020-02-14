#!/bin/bash


for subdir in `ls -d 20??????_??????`
do
   cd $subdir
  
   # merge :
   # -H disables dumping of .bin files 
   # -i 0.2831 is integration time in seconds when --channel_samples=262144  samples (1.08 usec each) are collected 
   merge_path=`which hdf5_to_uvfits_all.sh`
   echo "bash $merge_path -i 0.2831 -n 8140 -d merged/ -H -S 0 > merge.out"
   bash $merge_path -i 0.2831 -n 8140 -d merged/ -H -S 0 > merge.out 
   
   # move to separate sub-channel dirs :
   echo "~/aavs-calibration/sensitivity/daq/mvch.sh"
   ~/aavs-calibration/sensitivity/daq/mvch.sh      
      
   echo "~/aavs-calibration/sensitivity/daq/convert.sh"
   ~/aavs-calibration/sensitivity/daq/convert.sh
      

   cd ..
done
