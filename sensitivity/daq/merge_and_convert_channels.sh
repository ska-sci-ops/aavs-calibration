#!/bin/bash

template="?? ???"
if [[ -n "$1" && "$1" != "-" ]]; then
   template="$1"
fi

pwd

for ch in `ls -d ${template}`
do
   echo
   echo "Processing channel $ch"
   cd ${ch}
   pwd
   mkdir -p merged/
  
   # merge :
   # -H disables dumping of .bin files 
   # -i 0.2831 is integration time in seconds when --channel_samples=262144  samples (1.08 usec each) are collected 
   merge_path=`which hdf5_to_uvfits_all.sh`
   echo "bash $merge_path -i 0.2831 -n 8140 -d merged/ -H -S 0 > merge.out"
   bash $merge_path -i 0.2831 -n 8140 -d merged/ -H -S 0 > merge.out 
   
   # move to separate sub-channel dirs :
   cd merged/
   echo "/usr/local/bin/hdf2uvfits_zenith.sh \"-f ${ch}\""
   /usr/local/bin/hdf2uvfits_zenith.sh "-f ${ch}"   
   cd ../
      

   cd ..
done
