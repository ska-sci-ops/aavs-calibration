#!/bin/bash

channel=204
if [[ -n "$1" && "$1" != "-" ]]; then
   channel=$1
fi
freq_mhz=`echo $channel | awk '{printf("%.6f\n",$1*(400.00/512.00));}'`

template="last_calibration_???_fitted.txt"
if [[ -n "$2" && "$2" != "-" ]]; then
   template="$2"
fi

outfile="calsol_merged.txt"
if [[ -n "$3" && "$3" != "-" ]]; then
   outfile="$3"
fi

if [[ -s ${outfile} ]]; then
   echo "mv ${outfile} ${outfile}.backup"
   mv ${outfile} ${outfile}.backup
fi   

# frequency channel 204 = 159.3750 MHz
echo "# frequency channel ${channel} = ${freq_mhz} MHz" > ${outfile}
echo "# ANT AMP_XX PHASE_XX AMP_YY PHASE_YY AMP_XY PHASE_XY AMP_YX PHASE_YX" >> ${outfile}

for calfile in `ls ${template}`
do
   # ant=`head -1 ${calfile} | awk '{print $4;}'`
   ant=`echo ${calfile} | cut -b 18-20 | awk '{printf("%d\n",$1);}'`
   cal=`cat $calfile | awk -v channel=${channel} '{if( $1 != "#" && $1 == channel ){print $2" "$3" "$4" "$5" "$6" "$7" "$8" "$9;}}'`
   
   echo "$ant $cal" 
   
   echo "$ant $cal 0.00 0.00 0.00 0.00" >> ${outfile}
done
