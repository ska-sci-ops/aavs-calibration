#!/bin/bash

#############
# convert merged TPM output voltages to uvfits files with 2 averages each of approximately 0.14 seconds
# apply the known array configuration and flags to the raw data
# create a single dataset for calibration and apply that calibration to all data
############

echo "Starting TPM voltage dump processing"
date

# check that miriad environment is set up
if [[ -z "${MIR}" ]]; then
  echo "ERROR: miriad environment is not set up"
  exit 1
fi
if [[ -z "$AAVSCAL" ]]; then
  echo "ERROR: AAVSCAL environment variable is not set"
  exit 1
fi

# try to extract coarse channel from directory name
cc_dir=`pwd | tr -s '_/' '\n' | grep ch[0-9][0-9] | tr -d 'ch'`
# try to extract corase channel from data
firstfile=`ls -t *.hdf5 | head -1`
cc_dat=`h5dump -a /root/channel_id "$firstfile" | head -6 | tail -1 | cut -f 2 -d ":" | tr -d [:blank:]`

if [ "${cc_dat}" != "${cc_dir}" ] ; then
  echo "WARNING: extracted coarse channel from data (${cc_dat}) does not agree with directory (${cc_dir})"
fi
cc=${cc_dir}
echo "Detected coarse channel ${cc_dir}"

# try to detect which array the data is from
arr="eda2"
if [ `hostname` == "aavs2-server" ] ; then
  arr="aavs2"
fi

# try to extract start date from directory name. Assumes we're in the "merged" subdirectory
parentdir=`dirname $PWD`
fulldate=`basename $parentdir | cut -f 1-3 -d "_" | tr -d _`
obsstartunix=`date -u --date=$fulldate +%s`
echo "Extracted observation date ${fulldate} with unix start day of ${obsstartunix}"

corr_av=4096    # number of averages to do in correlator
corr_ch=32      # number of fine channels in correlator
cc_bw=925926    # coarse channel BW in Hz
corrinttime=`echo $corr_av $corr_ch $cc_bw | awk '{ printf "%.3f\n",$1*$2/$3 }'`
echo "Correlator integration time: $corrinttime"

mypipe=`mktemp -u`
mkfifo $mypipe
# make L-files
for hdffile in `ls channel_cont_20*.hdf5` ; do
  bname=`basename $hdffile _0.hdf5`
  echo "Processing $bname"
  if [ -f ${bname}.LACSPC ] ; then
    echo "Skipping existing output for $f"
    continue
  fi
  nice $AAVSCAL/h5rawdump_merged.py  -o $mypipe -i $hdffile &
  nice corr_multi_complex -c 32 -n 512 -w 10 -o $bname -t 2 -d -a 4096 -t 2 -i $mypipe
done
rm $mypipe

# extract times from files in same format as hdf2Lfile.sh
for f in *.hdf5 ; do
  bname=`basename $f _0.hdf5`
  echo "Processing $bname"
  h5dump -g sample_timestamps -b -o /tmp/ts $f
  startunix=`od -A none -t f8 /tmp/ts | head -1 | cut -f1 -d .`
  startunixfixed=$((startunix + offset_hours*3600))
  echo "Start unix time of data: $startunixfixed"
  echo "$startunixfixed" > ${bname}_ts_unix.txt
done

###########
#Process a single solar cal
###########
mkdir SunCal
cd SunCal

cp -s $AAVSCAL/config/${arr}/antenna_locations.txt antenna_locations.txt
cp $AAVSCAL/config/${arr}/instr_config.txt instr_config.txt
cp -s $AAVSCAL/config/${arr}/header.txt header.txt

#select a file near midday for solar calibration based on file name. Note that after 2020-04-06 the file name
# convention changed to be based on UTC not local time
if [ $obsstartunix -lt 1586217600 ] ; then
  middayfile=`ls ../channel_cont_*_43*_0.hdf5 | head -1`
else
  middayfile=`ls ../channel_cont_*_14*_0.hdf5 | head -1`
fi

sunhdf=`basename $middayfile _0.hdf5`
ln -s ../${sunhdf}_ts_unix.txt
ln -s ../${sunhdf}.LCCSPC
cp ../${sunhdf}.LACSPC .

startunix=`cat ${sunhdf}_ts_unix.txt`

sunpos=`python $AAVSCAL/sunpos.py $startunix`
sunra=`echo $sunpos | cut -f 1 -d " "`
sundec=`echo $sunpos | cut -f 2 -d " "`

Lfile2uvfits_eda.sh -i $corrinttime -n 2 -N 512 -C $corr_ch -f $cc_dir -R $sunra -D $sundec $sunhdf

obsid=`ls chan_${cc_dir}_20*.uvfits | head -1`
src=sun${cc_dir}

# calculate the approximate system temp and system gain. Not strictly necessary, but may
# help with propoer noise-weighted calibration
# calculate approximate systemp as 180*(180/f)^2.55 + 50
systemp=`echo $cc_dir | awk '{ printf "%.1f\n", 180.0*(180/($1*0.781250))^2.55 + 50 }'`
# rough estimate of Ae for dipole/SKALA in sparse regime. Goes down at lambda^2 just due to collecting area
# of a dipole. Use the Ae at 140 MHz as reference, which is about 2.3 m^2 for both
Ae=2.3 # 140 MHz
if [ $cc_ind -gt 180 ] ; then
  # scale Ae down in sparse regime
  Ae=`echo $cc_ind | awk '{ printf "%.1f\n", 2.3*($1*0.78125)^(-2) }'`
fi
jyperk=`echo $Ae | awk '{ printf "%.1f\n", 2761./$1 }'`

rm -rf ${src}.uv
fits op=uvin in=${obsid} out=${src}.uv options=compress
puthd in=${src}.uv/jyperk value=$jyperk
puthd in=${src}.uv/systemp value=$systemp

if [ $cc_dir -lt 192 ] ; then
  # reduce uv cut range for really low frequencies. Really only works when Sun is the only thing up at these freqs
  umin=0.004
  if [ $cc_dir -lt 100 ] ; then
    umin=0.003
  fi
  mfcal vis=${src}.uv flux=51000,0.15,1.9 select='uvrange('$umin',1)' # f < 150 MHz
else
  mfcal vis=${src}.uv flux=51000,0.15,1.6 select='uvrange(0.005,1)' edge=2 # f > 150 MHz
fi
puthd in=${src}.uv/interval value=2.5

#optionally image the sun
robust=0.5
stokes=xx
imsize=256
if [ $cc_ind -lt 300 ] ; then
  imsize=512
fi
rm -rf ${src}_${stokes}.map ${src}.beam
invert vis=${src}.uv map=${src}_${stokes}.map imsize=${imsize},${imsize} beam=${src}.beam robust=$robust options=double,mfs stokes=${stokes}
rm -rf ${src}_${stokes}.clean ${src}_${stokes}.restor ${src}_${stokes}.maxen
clean map=${src}_${stokes}.map beam=${src}.beam out=${src}_${stokes}.clean niters=5000 speed=-1 cutoff=100
restor model=${src}_${stokes}.clean beam=${src}.beam map=${src}_${stokes}.map out=${src}_${stokes}.restor

#exit 0

#################
#process zenith obs
################
cd ..

cp -s $AAVSCAL/config/${arr}/antenna_locations.txt antenna_locations.txt
cp $AAVSCAL/config/${arr}/instr_config.txt instr_config.txt
cp -s $AAVSCAL/config/${arr}/header.txt header.txt

la_chunksize=$((512*4))
lc_chunksize=$((512*511*8/2))
nchunks=2
rawaver=1
int_time=`echo $rawaver $corrinttime | awk '{ printf "%f\n",$1*$2 }'`

for hdffile in `ls -tr *.hdf5` ; do
    bname=`basename $hdffile _0.hdf5`
    echo "Processing file $hdffile"
    nice Lfile2uvfits_eda.sh -f ${cc_dir} -C ${corr_ch} -i ${int_time} -n $nchunks -N 512 "$bname"
done

for uvfitsfile in `ls chan_*.uvfits` ; do
    src=`basename $uvfitsfile .uvfits`
    echo "Processing $uvfitsfile to ${src}.uv"
    rm -rf ${src}.uv ${src}_XX.uv ${src}_YY.uv
    fits op=uvin in="$uvfitsfile" out="${src}.uv" options=compress
    puthd in=${src}.uv/jyperk value=${jyperk}
    puthd in=${src}.uv/systemp value=${systemp}
done

# apply cal
for uvfitsfile in `ls chan_*.uvfits` ; do
    src=`basename $uvfitsfile .uvfits`
    gpcopy vis=SunCal/sun${cc_dir}.uv out=${src}.uv
done

