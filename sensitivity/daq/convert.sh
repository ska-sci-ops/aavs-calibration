#!/bin/bash

for ch in `ls -d ?? ???`
do
   cd ${ch}
   echo "/usr/local/bin/hdf2uvfits_zenith.sh "-f ${ch}""
   /usr/local/bin/hdf2uvfits_zenith.sh "-f ${ch}"   
   cd ../
done
