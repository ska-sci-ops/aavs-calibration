#!/bin/bash
# make a sky model for AAVS1 calibration based on the Haslam map and sun

freq_mhz=159.375
lst=-1
unixtime=-1
beamtype="SKALA2"

function print_usage {
  echo "Usage:"
  echo "$0 [options] chan_index"
  echo -e "\t-f freq\tFrequency in MHz. Default: ${freq_mhz}"
  echo -e "\t-T time\tunix time. No default"
  echo -e "\t-B type\tBeam type: EDA, SKALA2 or SKALA4. Default: $beamtype" 
}

# parse command-line options
while getopts ":f:L:T:B:" opt; do
  case ${opt} in
    f)
      freq_mhz=${OPTARG}
      echo "user specified frequency ${freq_mhz} MHz"
      ;;
    T)
      unixtime=${OPTARG}
      ;;
    B)
      beamtype=${OPTARG}
      echo "Using beam type $beamtype"
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
if [ $unixtime -eq -1 ] ; then
  echo "ERROR: time is not set"
  exit 1
fi
# check that we can access the skymodel
if [[ -z "${AAVSCAL_SKYMODEL}" ]]; then
  echo "ERROR: AAVSCAL_SKYMODEL environment variable is not set"
  exit 1
fi
skymodel_basedir=${AAVSCAL_SKYMODEL}


lst=`${skymodel_basedir}/unixtime2lst.py $unixtime`
sunradec=`${skymodel_basedir}/sunpos.py $unixtime`
tmpdir=`mktemp -d`
pushd $tmpdir

# make a template sky model for this LST
fits op=xyin in=${skymodel_basedir}/pixscale_SIN_512x512.fits out=template.xy
lst_rad=`echo $lst | awk '{print $1*3.14159/12}'`
puthd in=template.xy/crval1 value=${lst_rad}

# regrid the Haslam CAR projection map using the template
# the units of this are strange: they are 0.1K, so a number like "167.0" in the map really means
# 16.7 K at 408 MHz.
echo "Regridding Haslam to sky"
regrid in=${skymodel_basedir}/haslam_CAR.xy out=sky.xy tin=template.xy tol=0 axes=1,2
lambda=`echo ${freq_mhz} | awk ' { print 300.0/$1 }'`
puthd in=sky.xy/object value='skymodel'

# calculate the scaling factor to scale Haslam to desired freq. This includes a term for the frequency
# scaling, and a term to convert temperature to Jy/pixel, where the pixel scale is for the centre of the
# map and a sky area scaling is applied with the template image below
scale_f=`echo ${freq_mhz} | awk ' { print 0.1*($1 / 408)^(-2.55) }'`
if [ ${scale_f} == "inf" ] ; then
  echo "ERROR: sky scaling factor error. Is freq_mhz set correctly?"
  exit 1
fi
# get pixel scale of sky image from header
pixscale=`gethd in=template.xy/cdelt2`  # pixel scale in radian
scale_p=`echo $pixscale $lambda | awk ' { print 2761.0*$1*$1/$2 }'`
if [ ${scale_p} == "inf" ] ; then
  echo "ERROR: pix scaling factor error."
  exit 1
fi
scale=`echo ${scale_p} ${scale_f} | awk ' { print $1*$2 }'`

# apply pixel scaling weight
echo "applying pixel scaling and frequency scaling corrections"
maths exp="sky.xy*template.xy*${scale}" out=skywt.xy
# export this to fits so that it can be used as reference image for sun
fits op=xyout in=skywt.xy out=skywt.fits

# add sun. Makes output file "skywt_sun.fits"
echo "Making sky model with sun"
${skymodel_basedir}/sun_add.py $unixtime ${freq_mhz} skywt.fits
result=$?
# if something went wrong or it wasn't daytime, just copy the exising sky image
if [ $result -ne 0 ] ; then
  cp skywt.fits skywt_sun.fits
fi

# apply beam average power pattern
nearest_MHz=`echo ${freq_mhz} | awk '{printf "%.0f",$1 }'`
# note pols in file names are swapped for SKALA2
beamyfits=${skymodel_basedir}/../BeamModels/SKALA2/SKALA2_Xpol_ortho_${nearest_MHz}.fits
beamxfits=${skymodel_basedir}/../BeamModels/SKALA2/SKALA2_Ypol_ortho_${nearest_MHz}.fits
if [ "$beamtype" = "EDA" ] ; then
  beamxfits="${skymodel_basedir}/../BeamModels/EDA/Xpol_EDA_ortho_${nearest_MHz}.fits"
  beamyfits="${skymodel_basedir}/../BeamModels/EDA/Ypol_EDA_ortho_${nearest_MHz}.fits"
fi
if [ "$beamtype" = "SKALA4" ] ; then
  beamxfits="${skymodel_basedir}/../BeamModels/SKALA4/SKALA4_Xpol_ortho_${nearest_MHz}.fits"
  beamyfits="${skymodel_basedir}/../BeamModels/SKALA4/SKALA4_Ypol_ortho_${nearest_MHz}.fits"
fi
echo "Applying beam patterns"
echo "Beam X: $beamxfits"
echo "Beam Y: $beamyfits"
fits op=xyin in=skywt_sun.fits out=skywt_sun.xy
fits op=xyin in="$beamyfits" out=beamy.xy
fits op=xyin in="$beamxfits" out=beamx.xy
maths exp="skywt_sun.xy*beamx.xy" out=Xsky.xy
maths exp="skywt_sun.xy*beamy.xy" out=Ysky.xy

# tidy up
popd
mv ${tmpdir}/Xsky.xy ${unixtime}_Xsky.xy
mv ${tmpdir}/Ysky.xy ${unixtime}_Ysky.xy
rm -rf ${tmpdir}

