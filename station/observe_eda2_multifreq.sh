#!/bin/bash

ra=275.21666667
if [[ -n "$1" && "$1" != "-" ]]; then
   ra=$1
fi

dec=-4.46027778
if [[ -n "$2" && "$2" != "-" ]]; then
   dec=$2
fi

name=J1820-0427
if [[ -n "$3" && "$3" != "-" ]]; then
   name=$3
fi

ux_start=1618601511
if [[ -n "$4" && "$4" != "-" ]]; then
   ux_start=$4
fi

dt=`date -d "1970-01-01 UTC $ux_start seconds" +"%Y%m%d"`
out_dir=/data/chris_lee/${dt}/${name}/
echo "mkdir -p ${out_dir}"
mkdir -p ${out_dir}
cd ${out_dir}
pwd

echo "observe_object_multifreq2.sh eda2 ${name} ${ra} ${dec} 900 ${out_dir} ${ux_start} \"90 130 170 190 204 230 250 270 290 370 390 410 430 450\" \"--mccs_db --flag_antennas=30,40,86,120,180,200,228,229,232,240\" > ${name}.out 2>&1"
observe_object_multifreq2.sh eda2 ${name} ${ra} ${dec} 900 ${out_dir} ${ux_start} "90 130 170 190 204 230 250 270 290 370 390 410 430 450" "--mccs_db --flag_antennas=30,40,86,120,180,200,228,229,232,240" > ${name}.out 2>&1
