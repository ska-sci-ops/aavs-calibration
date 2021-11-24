#!/bin/bash
# arguments:
# 1: hdf5 filename
# 2: integration time in L-file
# 3: RA hours (optional, default is zenith)
# 4: DEC degs (optional, default is zenith)
# dump_time=1.38240	# basic correlator integration time for 40000 averages
# dump_time=2.00016	# basic correlator integration time for 57875 averages
dump_time=1.9818086	# basic correlator integration time
ninp=512
nchan=32
nchunks=90
useradec=0
inttime=${dump_time}
chan=204
ra_hrs="-"
dec_degs="-"
debug="" # or -d
debug_flag=0
fractional_seconds=0
station_name=eda2

function print_usage {
  echo "Usage: "
  echo "Lfile2uvfits_eda.sh [options] L_filebasename "
  echo "    -i int_time   Default: $inttime. Basic correlator dump time: $dump_time"
  echo "    -n n_chunks   Default: $nchunks"
  echo "    -R ra_hours   Default: use zenith"
  echo "    -D dec_degs   Default: use zenith"
  echo "    -N n_inputs   Default: $ninp"
  echo "    -C n_chan     Default: $nchan"
  echo "    -f freq_chan  Default: $chan"
  echo "    -F allow fractional seconds -> different .uvfits file name, Default: $fractional_seconds"
  echo "    -d : enable debugging"
  echo "    -s station name Default: $station_name"
  exit
}

function generate_header_file 
{
#   n_scans=$1
   header_file=$1
   tstart=$2 
   dstart=$3 
   cent_freq=$4 
   inttime=$5
   useradec=$6
   ra_hrs=$7
   dec_degs=$8
   frac=$9
   frac_int=`echo $frac | awk '{printf("%02d",($1*100));}'`
   
   station_name_upper=`echo ${station_name} | awk '{print toupper($1)}'`
   
   echo "PARAMS : $header_file / $frac"
      

   # generate header file here (not copy from repo):
   echo "# AUTO-GENERATED $header_file file" > ${header_file}
   echo "FIELDNAME eda2cal" >> ${header_file}
   echo "TELESCOPE $station_name_upper      # telescope name like MWA, MOST, ATCA etc" >> ${header_file}
   echo "N_SCANS   $nchunks  # number of scans (time instants) in correlation products" >> ${header_file}
   echo "N_INPUTS  $ninp     # number of inputs into the correlation products" >> ${header_file}
   echo "N_CHANS   $nchan    # number of channels in spectrum" >> ${header_file}
   echo "CORRTYPE  B     # correlation type to use. 'C'(cross), 'B'(both), or 'A'(auto)" >> ${header_file}
   
# QUESTION to be sorted if it should be (400/512) or (400/512)*(32/27) - due to oversampling I am leaving at (400/512) for now ...   
#   echo "BANDWIDTH 0.925926  # total bandwidth in MHz" >> ${header_file}
   echo "BANDWIDTH 0.78125  # total bandwidth in MHz" >> ${header_file}
   
   if [ $useradec -ne 0 ] ; then
      # use values provided by user :
      echo "RA_HRS    $ra_hrs  # the RA at the *start* of the scan. (hours)" >> ${header_file}
      echo "DEC_DEGS  $dec_degs # the DEC of the desired phase centre (degs)" >> ${header_file}
   else
      # use default values
      echo "HA_HRS    -0.00833333  # the HA at the *start* of the scan. (hours)" >> ${header_file}
      echo "DEC_DEGS  -26.7033 # the DEC of the desired phase centre (degs)" >> ${header_file}
   fi   
   
   echo "INVERT_FREQ 0   # 1 if the freq decreases with channel number" >> ${header_file}

   # MS : 2021-11-24 - this change is for the transition period when AAVS2 has new firmware with correct sign and EDA2 still old sign (wrong convention):
   if [[ $station_name == "aavs2" || $station_name == "AAVS2" ]]; then
      echo "CONJUGATE 0     # conjugate the raw data to fix sign convention problem if necessary" >> ${header_file}
   else
      echo "CONJUGATE 1     # conjugate the raw data to fix sign convention problem if necessary" >> ${header_file}
   fi

   echo "GEOM_CORRECT 1  # apply geometric phase corrections when 1. Don't when 0" >> ${header_file}         
   
   echo "TIME    ${tstart}.${frac_int}" >> ${header_file}
   echo "DATE    $dstart" >> ${header_file}
   echo "FREQCENT ${cent_freq}" >> ${header_file}
   echo "INT_TIME $inttime" >> ${header_file}
}

if [ $# -eq 0 ] ; then
  print_usage
fi

# parse command-line args
if [ $# -lt 1 ] ; then print_usage ; fi
while getopts "hi:R:D:n:N:C:f:s:dF" opt; do
  case $opt in
    h)
        print_usage
        ;;
    d)
        debug="-d"
        debug_flag=1
        ;;
    F)
        fractional_seconds=1
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
    s)
        station_name=$OPTARG
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
# header=`mktemp`


Lfilebase="$1"
header=${Lfilebase}.hdr
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
if [ -e "${bname}_ts_unix.txt" ] ; then
  startunix=`cat ${bname}_ts_unix.txt`
else
  dt=`echo $bname | awk '{print substr($1,1,4)"-"substr($1,5,2)"-"substr($1,7,2);}'`
  tm=`echo $bname | awk '{print substr($1,10,2)":"substr($1,12,2)":"substr($1,14,2)}'`
  startunix=`date -u -d "$dt $tm" +%s`
fi
oname="chan_${chan}"
echo "stat -L --printf=\"%s\" $bname.LACSPC"
lacsize=`stat -L --printf="%s" $bname.LACSPC`
ntimes=$((lacsize/la_chunksize/nchunks))
if [ $ntimes -lt 1 ] ; then ntimes=1 ; fi
echo "Processing file $Lfilebase. There are $ntimes times ( = $lacsize / $la_chunksize / $nchunks ). Start unix time: $startunix"
for t in `seq 0 $((ntimes-1))` ; do
    # create a temporary header file for this dataset
#    if [ -e header.txt ] ; then
#      cp header.txt $header
#    else
#      cp header_ph1.txt $header 
#    fi

    echo "offset := $t * $timeinc"
    offset=`echo $t $timeinc | awk '{ printf "%.0f\n",$1*$2 }'`
    offset_int=`echo $t $timeinc | awk '{ printf "%d\n",$1*$2 }'`
    frac=`echo $t $timeinc $offset_int | awk '{ printf("%.2f\n",($1*$2-$3)); }'` # offset_int used to avoid negative fractions as "%.0f\n",$1*$2 rounds to the nearest integer (can go UP !)
    frac_int=`echo $frac | awk '{printf("%02d",($1*100));}'`
    start=$((startunix + offset))
    tstart=`date -u --date="@$start" +"%H%M%S"`
    dstart=`date -u --date="@$start" +"%Y%m%d"`
    echo "Making header for chunk $t. Time offset: $offset. Fraction: $frac Start time: $dstart $tstart"
    
    echo "generate_header_file $header $tstart $dstart ${cent_freq} $inttime $useradec $ra_hrs $dec_degs $frac"
    generate_header_file $header $tstart $dstart ${cent_freq} $inttime $useradec $ra_hrs $dec_degs $frac
        
    # chop out relevant section of L-files
    skip_bytes=$((nchunks*t))
    echo "DEBUG : skip_bytes = $skip_bytes = $nchunks * $t"
    
    echo "dd bs=${la_chunksize} skip=$skip_bytes count=$nchunks if=$bname.LACSPC > $lacspc"
    dd bs=${la_chunksize} skip=$skip_bytes count=$nchunks if=$bname.LACSPC > $lacspc
    
    echo "dd bs=${lc_chunksize} skip=$skip_bytes count=$nchunks if=$bname.LCCSPC > $lccspc"
    dd bs=${lc_chunksize} skip=$skip_bytes count=$nchunks if=$bname.LCCSPC > $lccspc
    
    echo "ls -al $lccspc $lacspc"
    ls -al $lccspc $lacspc
    
    # convert to uvfits
    startutc=`date -u --date=@${start} "+%Y%m%dT%H%M%S"`
    

# TODO : can we fix the time to have fractional seconds ?    
#    if [[ -s ${oname}_${startutc}.uvfits ]]; then
#        next=`ls ${oname}_${startutc}*.uvfits | wc -l`
#        next_str=`echo $next | awk '{printf("%03d",$1);}'`
        
#        echo "nice corr2uvfits -a $lacspc -c $lccspc -H $header -o ${oname}_${startutc}_${next_str}.uvfits"
#        nice corr2uvfits -a $lacspc -c $lccspc -H $header -o ${oname}_${startutc}_${next_str}.uvfits
#    else

#         echo "nice corr2uvfits -d -a $lacspc -c $lccspc -H $header -o ${oname}_${startutc}.uvfits"
#         nice corr2uvfits -d -a $lacspc -c $lccspc -H $header -o ${oname}_${startutc}.uvfits

        if [[ $fractional_seconds -gt 0 ]]; then
           echo "nice corr2uvfits $debug -a $lacspc -c $lccspc -H $header -o ${oname}_${startutc}${frac_int}.uvfits"
           nice corr2uvfits $debug -a $lacspc -c $lccspc -H $header -o ${oname}_${startutc}${frac_int}.uvfits
        else
           # this is default for backward compatibility if -F not enabled 
           echo "nice corr2uvfits $debug -a $lacspc -c $lccspc -H $header -o ${oname}_${startutc}.uvfits"
           nice corr2uvfits $debug -a $lacspc -c $lccspc -H $header -o ${oname}_${startutc}.uvfits
        fi
        
        if [[ $debug_flag -gt 0 ]]; then
           # ls created files for debug purposes 
           echo "ls -al $lacspc $lccspc $header *.uvfits"
           ls -al $lacspc $lccspc $header *.uvfits

           echo "$t : $header"
           cat $header
        fi
#    fi 
done

echo "rm -f $lacspc $lccspc"
rm -f $lacspc $lccspc

if [[ $debug_flag -le 0 ]]; then
   echo "rm -f ${header}"
   rm -f ${header}
fi

# keep headers for debugging 
#rm $header
