#!/bin/sh

tsfile=`mktemp`
hdffile="$1"
offset_hours=0
naverage=3

if [ $# -gt 1 ] ; then
  naverage="$2"
  if [ $naverage -lt 1 ] ; then
    echo "Bad naverage $naverage"
    exit 1
  fi
fi

echo "Processing file $hdffile with naverage $naverage"
bname=`basename $hdffile .hdf5`
if [ ! -f "${bname}.LACSPC" ] ; then
  nice python aavs_mwa_corr_converter.py -f $hdffile -o "$bname" -a $naverage
fi
# extract start unix time for data:
h5dump -g sample_timestamps -b -o $tsfile "$hdffile"
startunix=`od -A none -t f8 $tsfile | head -1 | cut -f1 -d .`
startunixfixed=$((startunix + offset_hours*3600))
echo "Start unix time of data: $startunixfixed"
echo "$startunixfixed" > ${bname}_ts_unix.txt

rm $tsfile
