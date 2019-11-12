#!/bin/bash

hdffile="$1"

echo "Processing file $hdffile"
bname=`basename $hdffile .hdf5`

echo "hdf2Lfile.sh ${hdffile}"
hdf2Lfile.sh ${hdffile}

echo "Lfile2casa.sh $bname"
Lfile2casa.sh $bname

