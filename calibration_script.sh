#!/usr/bin/env bash

default_dump_time=1.9818086
default_nav=1
default_data_dir=.
dump_time=${default_dump_time}
nav=${default_nav}
data_dir=${default_data_dir}
keep_intermediate=0
convert_hdf5_files=1

# Include binaries in calibration directory
#export PATH=$PATH:/home/aavs/randall_calibration
function print_usage {
  echo "Usage:"
  echo "$0 [options] chan_index"
  echo -e "\t-D data_dir\tdirectory to work in. Default: ${default_data_dir}"
  echo -e "\t-T dumptime\tcorrelator integration time. Default: ${default_dump_time}"
  echo -e "\t-N n_av \tpost correlator averaging that has been applied to data. Default: ${default_nav}"
  echo -e "\t-k  \tkeep intermediate data products for debugging"
  echo -e "\t-s  \tskip conversion from hdf5 files to uvfits (just calibrate using exisitng uvfits files). Default: ${convert_hdf5_files}"
}

#echo "Command line: $@"

# parse command-line options
while getopts ":D:T:N:k" opt; do
  case ${opt} in
    D)
      data_dir=${OPTARG}
      echo "user specified directory ${data_dir}"
      ;;
    T)
      dump_time=${OPTARG}
      echo "user specified dump time: ${dump_time}"
      ;;
    N)
      nav=${OPTARG}
      ;;
    k)
      keep_intermediate=1
      ;;
    s)
      convert_hdf5_files=0
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      print_usage
      exit -1
      ;;
  esac
done
shift $((OPTIND-1))

# check that miriad environment is set up
if [[ -z "${MIR}" ]]; then
  echo "ERROR: miriad environment is not set up"
  exit 1
fi

# Extract channel to work on
channel=$1
if [ "$channel" = "" ] ; then
  echo "invalid channel index $channel"
  exit 1
fi

# Go to directory where data is stored
cd "${data_dir}"
if [ $? -ne 0 ] ; then
  exit 1
fi
echo "channel: $channel. PWD: $PWD"

# Link some configuration files
ln -s /home/aavs/aavs-calibration/instr_config.txt
ln -s /home/aavs/aavs-calibration/antenna_locations.txt
ln -s /home/aavs/aavs-calibration/header_cal.txt header.txt

# Compute the integration time for the given dump time and integration skip (nav)
int_time=`echo $nav ${dump_time} | awk '{ printf "%.3f\n",$1*$2 }'`

# Convert all HDF files  for required channel to uvfits files with visibilities phased towards the sun
if [[ $convert_hdf5_files -gt 0 ]]; then
   echo "Executing conversion from hdf5 files to uvfits"
         
   for hdffile in `ls -tr *_${channel}_*.hdf5` ; do
      bname=`basename $hdffile .hdf5`
      hdf2Lfile.sh "$hdffile" $nav
      unixtime=`cat ${bname}_ts_unix.txt`
      radec=`python ~aavsuser/rwayth/sunpos.py $unixtime`
      Lfile2uvfits.sh "$hdffile" $int_time $radec
   done
else
   echo "WARNING : convert_hdf5_files=$convert_hdf5_files -> not executing conversion from hdf5 files to uvfits"
fi

# Unpack and flag
for uvfitsfile in `ls -tr chan_${channel}_*.uvfits` ; do
    src=`basename $uvfitsfile .uvfits`
    echo "Processing $uvfitsfile to ${src}.uv"
    rm -rf ${src}.uv ${src}_XX.uv ${src}_YY.uv
    fits op=uvin in="$uvfitsfile" out="${src}.uv" options=compress
    puthd in=${src}.uv/jyperk value=1310.0
    puthd in=${src}.uv/systemp value=200.0
    uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv
    uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv
done

# Perform self calibration on data
for uvfitsfile in `ls -tr chan_${channel}_*.uvfits` ; do
    src=`basename $uvfitsfile .uvfits`
    echo "Processing $uvfitsfile to ${src}.uv"
    selfcal vis=${src}_XX.uv select='uvrange(0.005,10)' options=amplitude,noscale refant=2 flux=100000
    selfcal vis=${src}_YY.uv select='uvrange(0.005,10)' options=amplitude,noscale refant=2 flux=100000
done

# Extract calibration solutions
outfile_amp="chan_${channel}_selfcal_amp"
outfile_pha="chan_${channel}_selfcal_pha"

tmpcal=`mktemp -d`
for uvfitsfile in `ls -tr chan_${channel}_*.uvfits` ; do
  src=`basename $uvfitsfile .uvfits`
  echo "Processing $uvfitsfile"
  for stokes in XX YY ; do
    gpplt vis=${src}_${stokes}.uv log=$tmpcal/aavs_gain_${stokes}_amp.txt
    gpplt vis=${src}_${stokes}.uv log=$tmpcal/aavs_gain_${stokes}_pha.txt yaxis=phase
    gain_extract_selfcal.sh $tmpcal/aavs_gain_${stokes}_amp.txt >> "${outfile_amp}_${stokes}.txt"
    gain_extract_selfcal.sh $tmpcal/aavs_gain_${stokes}_pha.txt >> "${outfile_pha}_${stokes}.txt"
  done
done

# Remove all generated files
if [ $keep_intermediate -ne 1 ] ; then
#  rm -fr *.uvfit
  rm -fr *ts_unix.txt *.uv
fi
for hdffile in `ls -tr *_${channel}_*.hdf5` ; do
  bname=`basename $hdffile .hdf5`
  rm -fr ${bname}.LACSPC ${bname}.LCCSPC 
done
rm -r $tmpcal
