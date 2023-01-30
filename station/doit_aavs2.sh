#!/bin/bash


export PATH=~/aavs-calibration/station/:~/aavs-calibration/station/pointing:$PATH
source /opt/aavs/python38/python/bin/activate

# 0630-2834
# observe_object_multifreq2.sh aavs2 J0630-2834 97.70416667 -28.57833333 900 /data/2022_12_02_pulsars_crab/J0630-2834_flagants_16ch_noamp/ 1670010930 "128" "--mccs_db --sign=-1 " 16 "--start_channel 0 --nof_channels 16 --dada -I" -1 0 /data/2022_12_02_pulsars_crab/aavs2_16channels_ch128.yml > J0630-2834_16channels_15min_flagants_sepdada_NoAmp.out 2>&1

# observe_object_multifreq2.sh aavs2 J0630-2834 97.70416667 -28.57833333 900 /data/2022_12_02_pulsars_crab/J0630-2834_flagants_16ch_amp/ 1668969921 "128" "--mccs_db --sign=-1 --apply_amplitudes " 16 "--start_channel 0 --nof_channels 16 --dada -I " -1 0 /data/2022_12_02_pulsars_crab/aavs2_16channels_ch128.yml > J0630-2834_16channels_15min_flagants_sepdada_Amp.out 2>&1

# observe_object_multifreq2.sh aavs2 J0630-2834 97.70416667 -28.57833333 900 /data/2022_12_02_pulsars_crab/J0630-2834_flagants_16ch_invamp/ 1668971121 "128" "--mccs_db --sign=-1 --apply_amplitudes --invert_amplitudes" 16 "--start_channel 0 --nof_channels 16 --dada -I " -1 0 /data/2022_12_02_pulsars_crab/aavs2_16channels_ch128.yml > J0630-2834_16channels_15min_flagants_sepdada_InvAmp.out 2>&1


# CRAB :
observe_object_multifreq2.sh aavs2 J0534+2200 83.63322083 22.01446111 900 /data/2023_01_29_pulsars_crab/J0534+2200_flagants_16ch_ch256_DelayRate1/ 1674997792 "256" "--mccs_db --sign=-1 " 16 "--start_channel 0 --nof_channels 16 --dada -I" -1 0 /data/2023_01_29_pulsars_crab/aavs2_16channels_ch256.yml 30 > J0534+2200_16channels_15min_flagants_sepdada_ch256_DelayRate1.out 2>&1
observe_object_multifreq2.sh aavs2 J0534+2200 83.63322083 22.01446111 900 /data/2023_01_29_pulsars_crab/J0534+2200_flagants_16ch_ch256_DelayRate0/ 1674997792 "256" "--mccs_db --sign=-1 " 16 "--start_channel 0 --nof_channels 16 --dada -I" -1 0 /data/2023_01_29_pulsars_crab/aavs2_16channels_ch256.yml 30 "--delta_time=0" > J0534+2200_16channels_15min_flagants_sepdada_ch256_DelayRate0.out 2>&1

# VELA :
# observe_object_multifreq2.sh aavs2 J0835-4510 128.8360 -45.1760 900 /data/2023_01_29_pulsars_crab/J0835-4510_flagants_16ch_ch256/ 1674664076 "256" "--mccs_db --sign=-1 " 16 "--start_channel 0 --nof_channels 16 --dada -I" -1 0 /data/2023_01_29_pulsars_crab/aavs2_16channels_ch256.yml 30 > vela_16channels_15min_flagants_sepdada_ch256.out 2>&1
# observe_object_multifreq2.sh aavs2 J0835-4510 128.8360 -45.1760 900 /data/2023_01_29_pulsars_crab/J0835-4510_flagants_16ch_ch410/ 1674664076 "410" "--mccs_db --sign=-1 " 16 "--start_channel 0 --nof_channels 16 --dada -I" -1 0 /data/2023_01_29_pulsars_crab/aavs2_16channels_ch410.yml 30 > vela_16channels_15min_flagants_sepdada_ch410.out 2>&1

# init station in normal mode without -IPB :
~/bin/init_station.sh


