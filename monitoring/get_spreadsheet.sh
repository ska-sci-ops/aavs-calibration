#!/bin/bash

eda2_url="https://docs.google.com/spreadsheets/d/1114rghywP0udKLJdQDPmPsf3XsMpjbDl/export?gid=652322881&format=csv"
aavs2_url="https://docs.google.com/spreadsheets/d/1114rghywP0udKLJdQDPmPsf3XsMpjbDl/export?gid=1726697402&format=csv"
skip_lines_aavs2=6
skip_lines_eda2=3

rm -f aavs2_tmp.csv eda2_tmp.csv

echo "TILE_NO,ANT_NO,POP_GRID_REF,LNA_X_SN,LNA_Y_SN,SMART_BOX_PORT,SMART_BOX_NUMBER,FIBRE_TAIL_NO,FEM_NO,FIBRE_CABLE_LEN,FNDH_FOBOT_PORT,ORIG_ORDER_OF_SDGI_CABLE,CFNDH_Bldg_Fibre_info,Bldg_Fibre_Colour,TPM_Location,TPM_Position,TPM_SN,TPM_IP,TPM_PORT_NO,WEBPAGE_PLOT_NO,MIRIAD_IDX,LNA_SN,Permanent_Comments,NULL1,NULL2,NULL3,NULL4,NULL5,NULL6,NULL7,NULL8,NULL9,NULL10,NULL11,NULL12,NULL13,NULL14,NULL15,NULL16,NULL17,NULL18" > header.txt

# AAVS2 spreadsheet :
echo "wget --no-check-certificate -O aavs2_tmp.csv $aavs2_url"
wget --no-check-certificate -O aavs2_tmp.csv $aavs2_url

# skip first lines :
aavs2_lines_tmp=`cat aavs2_tmp.csv | wc -l`
aavs2_lines=$(($aavs2_lines_tmp-$skip_lines_aavs2))
cat header.txt > aavs2.csv
# 22 -> 40
tail --lines ${aavs2_lines} aavs2_tmp.csv >> aavs2.csv # | awk -F "," '{for(i=1;i<=21;i++){printf("%s,",$i);}printf("\n");}' >> aavs2.csv

# EDA2 spreadsheet :
echo "wget --no-check-certificate -O eda2_tmp.csv $eda2_url"
wget --no-check-certificate -O eda2_tmp.csv $eda2_url

# skip first lines :
eda2_lines_tmp=`cat eda2_tmp.csv | wc -l`
eda2_lines=$(($eda2_lines_tmp-$skip_lines_eda2))
cat header.txt > eda2.csv
tail --lines ${eda2_lines} eda2_tmp.csv >> eda2.csv # | awk -F "," '{for(i=1;i<=21;i++){printf("%s,",$i);}printf("\n");}' >> eda2.csv
