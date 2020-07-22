#!/bin/bash

template="?? ???"
if [[ -n "$1" && "$1" != "-" ]]; then
   template="$1"
fi

station_name="eda2"
if [[ -n "$2" && "$2" != "-" ]]; then
   station_name=$2
fi

phase_center_sun=1
if [[ -n "$3" && "$3" != "-" ]]; then
   phase_center_sun=$3
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
   echo "bash $merge_path -i 0.2831 -n 8140 -d merged/ -H -S 0 -s ${station_name} > merge.out"
   bash $merge_path -i 0.2831 -n 8140 -d merged/ -H -S 0 -s ${station_name} > merge.out 
   
   # move to separate sub-channel dirs :
   cd merged/
   if [[ $phase_center_sun -gt 0 ]]; then
      echo "/usr/local/bin/hdf2uvfits_sun.sh \"-f ${ch} -s ${station_name}\""
      /usr/local/bin/hdf2uvfits_sun.sh "-f ${ch} -s ${station_name}"
   else
      echo "/usr/local/bin/hdf2uvfits_zenith.sh \"-f ${ch} -s ${station_name}\""
      /usr/local/bin/hdf2uvfits_zenith.sh "-f ${ch} -s ${station_name}"   
   fi
   cd ../
      

   cd ..
done
