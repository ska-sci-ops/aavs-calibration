#!/bin/bash
# arguments:
# 1: hdf5 filename
# 2: integration time in L-file
# 3: RA hours (optional, default is zenith)
# 4: DEC degs (optional, default is zenith)

# requires cotter_tiny to be compiled on the system : github.com/marcinsokolowski/cotter_tiny.git - it is a private repository at the moment, but might be changed if needed.
# assumes that cotter_tiny is installed in standard location (/usr/local/bin for example) - follow instructions in cotter_tiny README.md file

dump_time=1.38240	# basic correlator integration time for 40000 averages
dump_time=2.00016	# basic correlator integration time for 57875 averages
ninp=96
nchan=32
nchunks=90
useradec=0
inttime=${dump_time}
chan=204
antenna_locations_path=~/aavs-calibration/antenna_locations_eda2.txt
instr_path=~/aavs-calibration/instr_config_eda2.txt


function print_usage {
  echo "Usage: "
  echo "Lfile2casa.sh [options] L_filebasename "
  echo "    -i int_time   Default: $inttime. Basic correlator dump time: $dump_time"
  echo "    -n n_chunks   Default: $nchunks"
  echo "    -R ra_hours   Default: use zenith"
  echo "    -D dec_degs   Default: use zenith"
  echo "    -N n_inputs   Default: $ninp"
  echo "    -C n_chan     Default: $nchan"
  echo "    -f freq_chan  Default: $chan"
  echo "    -A antenna_location file Default: $antenna_locations_path"
  echo "    -I instr_config.txt file Default: $instr_path"
  exit
}

if [ $# -eq 0 ] ; then
  print_usage
fi

# parse command-line args
if [ $# -lt 1 ] ; then print_usage ; fi
while getopts "hi:R:D:n:N:C:f:A:I:" opt; do
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

    A)
        antenna_locations_path=$OPTARG
        ;;
    I)
        instr_path=$OPTARG
        ;;
    \?)
      echo "Invalid option: -$OPTARG" 1>&2
      print_usage
      ;;
  esac
done
shift $(expr $OPTIND - 1 )

echo "##################################"
echo "PARAMETERS:"
echo "##################################"
echo "instr_path = $instr_path"
echo "##################################"




la_chunksize=$((ninp*nchan*4))
lc_chunksize=$((ninp*(ninp-1)*nchan*8/2))

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
if [ -e "${bname}_ts_unix.txt" ] ; then
  startunix=`cat ${bname}_ts_unix.txt`
else
  dt=`echo $bname | awk '{print substr($1,1,4)"-"substr($1,5,2)"-"substr($1,7,2);}'`
  tm=`echo $bname | awk '{print substr($1,10,2)":"substr($1,12,2)":"substr($1,14,2)}'`
  startunix=`date -u -d "$dt $tm" +%s`
fi
oname="chan_${chan}"
lacsize=` stat --printf="%s" $bname.LACSPC`
ntimes=$((lacsize/la_chunksize/nchunks))
if [ $ntimes -lt 1 ] ; then ntimes=1 ; fi
echo "Processing file $Lfilebase. There are $ntimes times. Start unix time: $startunix"

echo "lfile2casa $Lfilebase ${Lfilebase}.ms -a ${antenna_locations_path} -i ${instr_path} -c ${chan}"
lfile2casa $Lfilebase ${Lfilebase}.ms -a ${antenna_locations_path} -i ${instr_path} -c ${chan}
