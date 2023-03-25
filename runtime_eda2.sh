# environment :
source /opt/aavs/python/bin/activate
export PATH=~/aavs-calibration/:~/aavs-calibration/station:$PATH
source /home/aavs/Software/miriad/miriad/MIRRC.sh
export PATH=$PATH:$MIRBIN:/usr/local/bin/
PGHOST=10.128.16.52


echo $PATH
which corr2uvfits

corr2uvfits
