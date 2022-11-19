#!/bin/bash

while [ 1 ];
do
   echo
   echo "---------------------------------------------------------"
   date
   current_ux=`date +%s`
   ls -ltr --full-time --time-style="+%s" *.hdf5 | awk -v current_ux=${current_ux} '{if($6<(current_ux-3600)){print "rm -f "$7}}' > rm!
#   ls -ltr *.hdf5 | head -64 | awk '{print "rm -f "$9;}' > rm!
   chmod +x rm!   
   echo "./rm!"
   cat ./rm!
   ./rm!
   
   echo "sleep 900"
   sleep 900 
done
