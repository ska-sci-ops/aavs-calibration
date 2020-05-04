#!/bin/bash

inttime=0.28
n_avg=8140
freq_ch=204
station_name=EDA2
convert_options="" # "-I 2"

ls *.hdf5 > new_hdf5_list.txt

# removed option -z to have Sun in the phase center :
echo "hdf5_to_uvfits_all.sh -c -l -i $inttime -n $n_avg -d "./" -N -f $freq_ch -l -L new_hdf5_list.txt -s ${station_name} $convert_options"
hdf5_to_uvfits_all.sh -c -l -i $inttime -n $n_avg -d "./" -N -f $freq_ch -l -L new_hdf5_list.txt -s ${station_name} $convert_options

echo "~/aavs-calibration/calibrate_uvfits.sh"
~/aavs-calibration/calibrate_uvfits.sh