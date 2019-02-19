#!/bin/sh

# utility script to convert raw hdf5 files into L-files, including an option to do some time
# averaging, which is passed to aavs_mwa_corr_converter.py (which does the real work)
# also extract the starting time for the data into a file ending in ts_unix.txt
# the start time is unix time (seconds since unix epoch)

offset_hours=0
naverage=3

print_usage () {
  echo "Usage:"
  echo "$1 hdf_file [n_averages] [offset_hours]"
  echo "       default n_average: $naverage"
  echo "       default offset_hours: $offset_hours"
  exit
}

if [ $# -eq 0 ] ; then
  print_usage "$0"
fi

tsfile=`mktemp`
hdffile="$1"

if [ $# -gt 1 ] ; then
  naverage="$2"
  if [ $naverage -lt 1 ] ; then
    echo "Bad naverage $naverage"
    exit 1
  fi
fi

if [ $# -gt 2 ] ; then
  offset_hours=$3
fi

echo "Processing file $hdffile with naverage $naverage"
bname=`basename $hdffile .hdf5`
if [ ! -f "${bname}.LACSPC" ] ; then
  nice aavs_mwa_corr_converter.py -f $hdffile -o "$bname" -a $naverage
fi
# extract start unix time for data:
h5dump -g sample_timestamps -b -o $tsfile "$hdffile"
startunix=`od -A none -t f8 $tsfile | head -1 | cut -f1 -d .`
startunixfixed=$((startunix + offset_hours*3600))
echo "Start unix time of data: $startunixfixed"
echo "$startunixfixed" > ${bname}_ts_unix.txt

rm $tsfile
