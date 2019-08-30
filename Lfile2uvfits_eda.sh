#!/bin/bash
# arguments:
# 1: hdf5 filename
# 2: integration time in L-file
# 3: RA hours (optional, default is zenith)
# 4: DEC degs (optional, default is zenith)
dump_time=1.38240	# basic correlator integration time for 40000 averages
dump_time=2.00016	# basic correlator integration time for 57875 averages
ninp=96
nchan=32
nchunks=90
useradec=0
inttime=${dump_time}
chan=204

function print_usage {
  echo "Usage: "
  echo "Lfile2uvfits.sh [options] L_filebasename "
  echo "    -i int_time   Default: $inttime. Basic correlator dump time: $dump_time"
  echo "    -n n_chunks   Default: $nchunks"
  echo "    -R ra_hours   Default: use zenith"
  echo "    -D dec_degs   Default: use zenith"
  echo "    -N n_inputs   Default: $ninp"
  echo "    -C n_chan     Default: $nchan"
  echo "    -f freq_chan  Default: $chan"
  exit
}

if [ $# -eq 0 ] ; then
  print_usage
fi

# parse command-line args
if [ $# -lt 1 ] ; then print_usage ; fi
while getopts "hi:R:D:n:N:C:f:" opt; do
  case $opt in
    h)
        print_usage
        ;;
    n)
        nchunks=$OPTARG
        ;;
    f)
        chan=$OPTARG
        ;;
    N)
        ninp=$OPTARG
        ;;
    C)
        nchan=$OPTARG
        ;;
    i)
        inttime=$OPTARG
        ;;
    R)
        ra_hrs=$OPTARG
        useradec=1
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


la_chunksize=$((ninp*nchan*4))
lc_chunksize=$((ninp*(ninp-1)*nchan*8/2))

lacspc=`mktemp`
lccspc=`mktemp`
header=`mktemp`

Lfilebase="$1"
cent_freq=`echo $chan |  awk '{ printf "%f\n",$1*0.781250 }'`

if [ $# -gt 1 ]; then
  inttime=$2
fi
if [ $# -gt 3 ] ; then
  ra_hrs=$3
  dec_degs=$4
  useradec=1
fi

timeinc=`echo $nchunks ${inttime} | awk '{ printf "%f\n",$1*$2 }'`

bname=$Lfilebase
# extract start unix time for data:
dt=`echo $bname | awk '{print substr($1,1,4)"-"substr($1,5,2)"-"substr($1,7,2);}'`
tm=`echo $bname | awk '{print substr($1,10,2)":"substr($1,12,2)":"substr($1,14,2)}'`
startunix=`date -u -d "$dt $tm" +%s`
oname="chan_${chan}"
lacsize=` stat --printf="%s" $bname.LACSPC`
ntimes=$((lacsize/la_chunksize/nchunks))
if [ $ntimes -lt 1 ] ; then ntimes=1 ; fi
echo "Processing file $Lfilebase. There are $ntimes times"
for t in `seq 0 $((ntimes-1))` ; do
    # create a temporary header file for this dataset
    cp header_ph1.txt $header 
    offset=`echo $t $timeinc | awk '{ printf "%.0f\n",$1*$2 }'`
    start=$((startunix + offset))
    tstart=`date -u --date="@$start" +"%H%M%S"`
    dstart=`date -u --date="@$start" +"%Y%m%d"`
    echo "Making header for chunk $t. Time offset: $offset. Start time: $dstart $tstart"
    echo -e "\nTIME    $tstart" >> $header
    echo "DATE    $dstart" >> $header
    echo "FREQCENT ${cent_freq}" >> $header
    echo "INT_TIME $inttime" >> $header
    echo "N_SCANS $nchunks" >> $header
    # update the number of scans in file
#    sed -i 's/^N_SCANS/\#N_SCANS/ $header'
    if [ $useradec -ne 0 ] ; then
      # remove any existing default HA setting
      sed -i 's/^HA_HRS/#&/' $header
      sed -i 's/^DEC_DEGS/#&/' $header
      # insert new coords for phase centre
      echo "RA_HRS $ra_hrs" >> $header
      echo "DEC_DEGS $dec_degs" >> $header
    fi
    # chop out relevant section of L-files
    dd bs=${la_chunksize} skip=$((nchunks*t)) count=$nchunks if=$bname.LACSPC > $lacspc
    dd bs=${lc_chunksize} skip=$((nchunks*t)) count=$nchunks if=$bname.LCCSPC > $lccspc
    # convert to uvfits
    startutc=`date -u --date=@${start} "+%Y%m%dT%H%M%S"`
    
    if [[ -s ${oname}_${startutc}.uvfits ]]; then
        # TODO : can we fix the time to have fractional seconds ?
        count=`ls ${oname}_${startutc}*.uvfits | wc -l`
        next=$(($count+1))
        next_str=`echo $next | awk '{printf("%03d",$1);}'`
        
        echo "nice corr2uvfits -a $lacspc -c $lccspc -H $header -o ${oname}_${startutc}_${next_str}.uvfits"
        nice corr2uvfits -a $lacspc -c $lccspc -H $header -o ${oname}_${startutc}_${next_str}.uvfits
    else
        echo "nice corr2uvfits -a $lacspc -c $lccspc -H $header -o ${oname}_${startutc}.uvfits"
        nice corr2uvfits -a $lacspc -c $lccspc -H $header -o ${oname}_${startutc}.uvfits
    fi 
done

rm $lacspc
rm $lccspc
#rm $header
