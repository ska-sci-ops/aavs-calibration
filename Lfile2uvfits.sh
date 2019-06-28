#!/bin/bash
# arguments:
# 1: hdf5 filename
# 2: integration time in L-file
# 3: RA hours (optional, default is zenith)
# 4: DEC degs (optional, default is zenith)
dump_time=1.9818086	# basic correlator integration time
#timeinc=59.4925
la_chunksize=$((512*4))
lc_chunksize=$((512*511*8/2))
nchunks=5
useradec=0
inttime=9.90903

function print_usage {
  echo "Usage: "
  echo "Lfile2uvfits.sh [options] hdf_filename "
  echo "    -i int_time   Default: $inttime. Basic correlator dump time: $dump_time"
  echo "    -n n_chunks   Default: $nchunks"
  echo "    -R ra_hours   Default: use zenith"
  echo "    -D dec_degs   Default: use zenith"
  exit
}

if [ $# -eq 0 ] ; then
  print_usage
fi

# parse command-line args
if [ $# -lt 1 ] ; then print_usage ; fi
while getopts "hi:R:D:n:" opt; do
  case $opt in
    h)
        print_usage
        ;;
    n)
        nchunks=$OPTARG
        ;;
    i)
        inttime=$OPTARG
        ;;
    R)
        ra_hrs=$OPTARG
        ;;
    D)
        dec_degs=$OPTARG
        ;;
    \?)
      echo "Invalid option: -$OPTARG" 1>&2
      print_usage
      ;;
  esac
done
shift $(expr $OPTIND - 1 )


lacspc=`mktemp`
lccspc=`mktemp`
header=`mktemp`

hdffile="$1"
chan=`echo $hdffile | cut -f 3 -d _`
if [ $chan -lt 1 ] ; then
  echo "Unable to find channel index from hdf file name" 1>&2
  exit 1
fi
cent_freq=`echo $chan |  awk '{ printf "%f\n",$1*0.781250 }'`

if [ $# -gt 1 ] ; then
  inttime=$2
fi
if [ $# -gt 3 ] ; then
  ra_hrs=$3
  dec_degs=$4
  useradec=1
fi

timeinc=`echo $nchunks ${inttime} | awk '{ printf "%f\n",$1*$2 }'`

bname=`basename $hdffile .hdf5`
# extract start unix time for data:
startunix=`cat ${bname}_ts_unix.txt`
oname="chan_${chan}"
lacsize=` stat --printf="%s" $bname.LACSPC`
ntimes=$((lacsize/la_chunksize/nchunks))
if [ $ntimes -lt 1 ] ; then ntimes=1 ; fi
echo "Processing file $hdffile. There are $ntimes times"
for t in `seq 0 $((ntimes-1))` ; do
    # create a temporary header file for this dataset
    cp header.txt $header 
    offset=`echo $t $timeinc | awk '{ printf "%.0f\n",$1*$2 }'`
    start=$((startunix + offset))
    tstart=`date -u --date="@$start" +"%H%M%S"`
    dstart=`date -u --date="@$start" +"%Y%m%d"`
    echo "Making header for chunk $t. Time offset: $offset. Start time: $dstart $tstart"
    echo -e "\nTIME    $tstart" >> $header
    echo "DATE    $dstart" >> $header
    echo "FREQCENT ${cent_freq}" >> $header
    echo "INT_TIME $inttime" >> $header
    # update the number of scans in file
    sed -i 's/^N_SCANS/#N_SCANS/ $header'
    if [ $useradec -ne 0 ] ; then
      # remove any existing default HA setting
      sed -i 's/^HA_HRS/#&/' $header
      # insert new coords for phase centre
      echo "RA_HRS $ra_hrs" >> $header
      echo "DEC_DEGS $dec_degs" >> $header
    fi
    # chop out relevant section of L-files
    dd bs=${la_chunksize} skip=$((nchunks*t)) count=$nchunks if=$bname.LACSPC > $lacspc
    dd bs=${lc_chunksize} skip=$((nchunks*t)) count=$nchunks if=$bname.LCCSPC > $lccspc
    # convert to uvfits
    startutc=`date -u --date=@${start} "+%Y%m%dT%H%M%S"`
    nice corr2uvfits -a $lacspc -c $lccspc -H $header -o ${oname}_${startutc}.uvfits
done

rm $lacspc
rm $lccspc
rm $header
