#!/bin/bash

list_file=uvfits_list
do_mfcal_object="sun" # use mfcal with proper solar flux scale (as in Randall's script to get SEFD and other proper flux scale)
channel=204
reference_antenna=3
control_image=1
save_calsolutions=1
do_xx_yy=0 # WARNING : do not use =1 as this when applied to other observation (calibration transfer) produces wrong flux scale !!!

export PATH=~/aavs-calibration:$PATH

if [[ ! -s ${list_file} ]]; then
   echo "WARNING : UV FITS file list does not exist -> using all"
   
   echo "ls *.uvfits > ${list_file}"
   ls *.uvfits > ${list_file}
fi

# 
for uvfitsfile in `cat ${list_file}` ; 
do
    src=`basename $uvfitsfile .uvfits`
    echo "Processing $uvfitsfile to ${src}.uv"
    
    echo "rm -rf ${src}.uv ${src}_XX.uv ${src}_YY.uv"
    rm -rf ${src}.uv ${src}_XX.uv ${src}_YY.uv
    
    
    echo "fits op=uvin in=\"$uvfitsfile\" out=\"${src}.uv\" options=compress"
    fits op=uvin in="$uvfitsfile" out="${src}.uv" options=compress
    
    echo "puthd in=${src}.uv/jyperk value=1310.0"
    puthd in=${src}.uv/jyperk value=1310.0
    
    echo "puthd in=${src}.uv/systemp value=200.0"
    puthd in=${src}.uv/systemp value=200.0

    if [[ $do_xx_yy -gt 0 ]]; then    
      echo "uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv"
      uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv
    
      echo "uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv"
      uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv
    fi

    # MFCAL : 
    if [[ $channel -gt 192 ]]; then # f > 150 MHz (192 *(400/512) = 150 MHz ) :
       echo "Channel = $channel > 192 -> using the high-frequency power law:"

       if [[ $do_xx_yy -gt 0 ]]; then
          # mfcal on XX and YY or rather uvcat to split .uv -> _XX.uv and _YY.uv ?
          # current way is a bit in-efficient, so I will change it later
          echo "mfcal vis=${src}_XX.uv flux=51000,0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna}"  
          mfcal vis=${src}_XX.uv flux=51000,0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna} # f > 150 MHz

          echo "mfcal vis=${src}_YY.uv flux=51000,0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna}"  
          mfcal vis=${src}_YY.uv flux=51000,0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna} # f > 150 MHz          
       else
          echo "mfcal vis=${src}.uv flux=51000,0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna}"
          mfcal vis=${src}.uv flux=51000,0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna} # f > 150 MHz          
       fi
    else
        # verifyed on 2020-04-23 :
        # Lower limit of 0.005 kLambda means 10m at 150 MHz to make it 10 m everywhere use the following formula
        #    It comes from B_min = 10m expressed in kLambda -> (B_min/Lambda[m])*Lambda[m] = (B_min/Lambda[m])*(kLambda/1000.00) as kLambda = Lambda[m]/1000.00
        #    and Lambda[m] = 300 / ( (400/512)*ch ) [m] 
        # below 150 MHz the uvrange has to be different as otherwise we can end up with 0 baselines 
        # I set limit to B>10m and calculate 
        min_klambda=`echo $channel | awk '{print ($1*(400.00/512.00))/30000.00;}'`

        echo "Channel = $channel <= 192 -> using the low-frequency power law, lower uvrange limit = $min_klambda kLambda"

        if [[ $do_xx_yy -gt 0 ]]; then
           # mfcal on XX and YY or rather uvcat to split .uv -> _XX.uv and _YY.uv ?
           # current way is a bit in-efficient, so I will change it later
           echo "mfcal vis=${src}_XX.uv flux=51000,0.15,1.9 select=\"uvrange($min_klambda,1)\" refant=${reference_antenna}"
           mfcal vis=${src}_XX.uv flux=51000,0.15,1.9 select="uvrange($min_klambda,1)" refant=${reference_antenna} # f < 150 MHz

           echo "mfcal vis=${src}_YY.uv flux=51000,0.15,1.9 select=\"uvrange($min_klambda,1)\" refant=${reference_antenna}"
           mfcal vis=${src}_YY.uv flux=51000,0.15,1.9 select="uvrange($min_klambda,1)" refant=${reference_antenna} # f < 150 MHz                          
        else
           echo "mfcal vis=${src}.uv flux=51000,0.15,1.9 select=\"uvrange($min_klambda,1)\" refant=${reference_antenna}"
           mfcal vis=${src}.uv flux=51000,0.15,1.9 select="uvrange($min_klambda,1)" refant=${reference_antenna} # f < 150 MHz
        fi
    fi
    
    if [[ $do_xx_yy -gt 0 ]]; then
       # set validity of calibraton solutions to 365 days !!!
       echo "puthd in=${src}_XX.uv/interval value=365"
       puthd in=${src}_XX.uv/interval value=365

       echo "puthd in=${src}_YY.uv/interval value=365"
       puthd in=${src}_YY.uv/interval value=365
    else
       # set validity of calibraton solutions to 365 days !!!
       echo "puthd in=${src}.uv/interval value=365"
       puthd in=${src}.uv/interval value=365   
    fi

    if [[ $control_image -gt 0 || $save_calsolutions -gt 0 ]]; then
       if [[ ! -d ${src}_XX.uv ]]; then
          echo "uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv"
          uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv
       fi   

       if [[ ! -d ${src}_YY.uv ]]; then
          echo "uvcat vis=${src}.uv stokes=xx out=${src}_YY.uv"
          uvcat vis=${src}.uv stokes=xx out=${src}_YY.uv
       fi

       if [[ $save_calsolutions -gt 0 ]]; then
          echo "INFO : saving calibration solutions to *.txt files"
       
          # save solutions :
          for stokes in `echo "XX YY"`
          do
             gpplt vis=${src}_${stokes}.uv log=aavs_gain_${stokes}_amp.txt
             gpplt vis=${src}_${stokes}.uv log=aavs_gain_${stokes}_pha.txt yaxis=phase
             gain_extract_selfcal.sh aavs_gain_${stokes}_amp.txt >> "amp_${stokes}.txt"
             gain_extract_selfcal.sh aavs_gain_${stokes}_pha.txt >> "phase_${stokes}.txt"
          done
       else
          echo "WARNING : saving calibration solutions to text files is not required"
       fi


       if [[ $control_image -gt 0 ]]; then       
          echo "INFO : creating control images"
        
          rm -fr ${src}_XX.map ${src}_XX.beam ${src}_YY.map ${src}_YY.beam
          echo "invert vis=${src}_XX.uv map=${src}_XX.map imsize=180,180 beam=${src}_XX.beam robust=-0.5 options=double,mfs" 
          invert vis=${src}_XX.uv map=${src}_XX.map imsize=180,180 beam=${src}_XX.beam robust=-0.5 options=double,mfs
       
          echo "invert vis=${src}_YY.uv map=${src}_YY.map imsize=180,180 beam=${src}_YY.beam robust=-0.5 options=double,mfs" 
          invert vis=${src}_YY.uv map=${src}_YY.map imsize=180,180 beam=${src}_YY.beam robust=-0.5 options=double,mfs
       
          echo "fits op=xyout in=${src}_XX.map out=${src}_XX.fits"
          fits op=xyout in=${src}_XX.map out=${src}_XX.fits
       
          echo "fits op=xyout in=${src}_YY.map out=${src}_YY.fits"
          fits op=xyout in=${src}_YY.map out=${src}_YY.fits
       else
          echo "WARNING : control images are not required"       
       fi
    fi
done
