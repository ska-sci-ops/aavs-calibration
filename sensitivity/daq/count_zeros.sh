#!/bin/bash

listfile="hdf5_list"
if [[ -n "$1" && "$1" != "-" ]]; then
   listfile=$1
fi

if [[ ! -s ${listfile} ]]; then
   ls *.hdf5 > hdf5_list
   listfile="hdf5_list"
fi


for hdf5file in `cat $listfile`
do
   # hdf5_correlator channel_cont_5_20191221_40040_0.hdf5 -d  -k channel_cont_5_20191221_40040_0.txt
   txtfile=${hdf5file%%hdf5}txt
   
   echo "hdf5_correlator ${hdf5file} -d -k ${txtfile}"
   hdf5_correlator ${hdf5file} -d -k ${txtfile}
done

