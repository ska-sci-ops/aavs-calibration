#!/bin/bash

file=chan_204_selfcal_pha_XX.txt
if [[ -n "$1" && "$1" != "-" ]]; then
   file=$1
fi

phase0=0
if [[ -n "$2" && "$2" != "-" ]]; then
   phase0=$2
fi


awk -v phase0=${phase0} '{for(i=3;i<=NF;i++){diff=(($i)-phase0);if(diff<-180){diff+=360.00;}if(diff>180){diff-=360.00;}printf("%d %.2f\n",(i-3),diff);}}' ${file}
