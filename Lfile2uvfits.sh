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
station_name_upper=EDA2

function print_usage {
  echo "Usage: "
  echo "Lfile2uvfits.sh [options] hdf_filename "
  echo "    -i int_time   Default: $inttime. Basic correlator dump time: $dump_time"
  echo "    -n n_chunks   Default: $nchunks"
  echo "    -R ra_hours   Default: use zenith"
  echo "    -D dec_degs   Default: use zenith"
  echo "    -S STATION_NAME , in capitals , Default : $station_name_upper"
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
        useradec=1
        ;;
    S)
        station_name_upper=$OPTARG
        echo "DEBUG : -S option station_name_upper = $station_name_upper"
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
# header=`mktemp`

hdffile="$1"
chan=`echo $hdffile | cut -f 3 -d _`
if [ $chan -lt 1 ] ; then
  echo "Unable to find channel index from hdf file name" 1>&2
  exit 1
fi
cent_freq=`echo $chan |  awk '{ printf "%f\n",$1*0.781250 }'`
header=${hdffile}.hdr

if [ $# -gt 1 ] ; then
  inttime=$2
fi
if [ $# -gt 3 ] ; then
  ra_hrs=$3
  dec_degs=$4
  useradec=1
fi

timeinc=`echo $nchunks ${inttime} | awk '{ printf "%f\n",$1*$2 }'`

# New vs. old firmware and sign flip :
# Check the dates to work ok for old data !!!
new_firmware_start_ux=1637712000
if [[ $station_name_upper == "EDA2" ]]; then
   # MS : 2022-11-23 : both EDA2 and AAVS2 use the same firmware now and it should be 0 for both:
   new_firmware_start_ux=1669161600
fi


echo "############################"
echo "PARAMETERS:"
echo "############################"
echo "chan    = $chan"
echo "inttime = $inttime"
echo "new_firmware_start_ux = $new_firmware_start_ux"
echo "station_name_upper = $station_name_upper"
echo "############################"

bname=`basename $hdffile .hdf5`
# extract start unix time for data:
startunix=`cat ${bname}_ts_unix.txt`
oname="chan_${chan}"
echo "stat -L --printf=\"%s\" $bname.LACSPC"
lacsize=`stat -L --printf="%s" $bname.LACSPC`
ntimes=$((lacsize/la_chunksize/nchunks))
echo "INFO : ntimes = $ntimes, lacsize = $lacsize , la_chunksize = $la_chunksize , nchunks = $nchunks , inttime = $inttime , timeinc = $timeinc"
if [ $ntimes -lt 1 ] ; then ntimes=1 ; fi

# header.txt : CONJUGATE base on the date of the data :
echo "DEBUG : comparing startunix=$startunix vs. new_firmware_start_ux = $new_firmware_start_ux"
if [[ $startunix -gt $new_firmware_start_ux ]]; then
   echo "INFO : $startunix > $new_firmware_start_ux -> stays CONJUGATE = 0"
else
   echo "INFO : $startunix <= $new_firmware_start_ux -> old data -> CONJUGATE set to 1 (sed)"       
   sed -i 's/CONJUGATE 0/CONJUGATE 1/' header.txt
fi

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
    sed -i 's/^N_SCANS/#N_SCANS/' $header
    echo "N_SCANS $nchunks" >> $header
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
    
    echo "nice corr2uvfits -a $lacspc -c $lccspc -H $header -I instr_config.txt -o ${oname}_${startutc}.uvfits"
    nice corr2uvfits -a $lacspc -c $lccspc -H $header -I instr_config.txt -o ${oname}_${startutc}.uvfits
done

rm $lacspc
rm $lccspc
# rm $header
