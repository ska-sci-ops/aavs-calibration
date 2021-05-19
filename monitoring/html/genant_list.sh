#!/bin/bash

ant=1 

while [[ $ant -le 256 ]]; 
do
   ant_str=`echo $ant | awk '{printf("%03d\n",$1);}'`
   
   echo "<li>Ant${ant_str}<a href=\"Ant${ant_str}_x.png\"><u>X polarisation</u></a> , <a href=\"Ant${ant_str}_y.png\"><u>Y polarisation</u></a>"

   ant=$(($ant+1))
done

