import math
import sys

freq=150.00
if len(sys.argv) > 1:
   freq = float(sys.argv[1])

freq0=150.00
if len(sys.argv) > 2:
   freq0 = float(sys.argv[2])
   
# 48898.8
flux0 = 51000
if len(sys.argv) > 3:
   flux0 = float(sys.argv[3])
   

# Quiet sun (http://extras.springer.com/2009/978-3-540-88054-7/06_vi4b_4116.pdf
# 4.1.1.6 Quiet and slowly varying radio emissions of the sun
# extras.springer.com )
# note change in spectral index of sun around 150 MHz, so better to use different
# power law at low vs high freqs
# MFCAL flux parameters : 51000,0.15,1.6
alpha=1.6
flux = flux0*pow(freq/freq0,alpha)

print("Flux( %.2f MHz) = %.4f Jy" % (freq,flux))


