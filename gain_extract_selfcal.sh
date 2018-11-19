#!/bin/bash 
###################
# extract gains from single pol data after selfcal
###################
lines_per_time=43   # for single pol selfcal solution
nlines=`cat $1 | wc -l`
ntimes=$((nlines / lines_per_time ))
for t in `seq 0 $((ntimes-1))` ; do
    #echo "Extracting time index $t"
    nskip=$((t*lines_per_time+5))
    tail -n +"$nskip" $1 | head -$lines_per_time | tr -d '\n' | tr -s ' '
    echo
done

