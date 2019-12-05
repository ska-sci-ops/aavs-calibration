# this scripts allows to calculate how to update delays in config files based on the newly calculated delays from the cal. solutions
# it still requires a bit of copy/pasting and editing, but hopefylly next iterations will be a bit more automatic ...

import numpy

# delays from recent calibration (for example 2019_12_05-15:27 ):
dt1 = [0, 0, 1, 1, 0, 0, -1, -1, 0, 0, -1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, -1, -1, 1, 1]
dt2 = [0, 0, 0, 0, -2, -2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, -1, -1, -1, -1, -2, -2, 1, 1]
dt3 = [10, 10, 11, 11, 10, 10, 12, 12, 11, 11, 9, 9, 11, 11, 11, 11, 10, 10, 9, 9, 10, 10, 9, 9, 9, 9, 11, 11, 11, 11, 10, 10]
dt4 = [1, 1, 1, 1, 2, 2, 4, 4, 2, 2, 1, 1, 0, 0, 1, 1, 0, 0, -1, -1, -2, -2, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]
dt5 = [0, 0, 0, 0, -1, -1, -1, -1, -1, -1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0]
dt6 = [0, 0, 0, 0, -1, -1, 1, 1, 0, 0, -2, -2, 44, 44, 1, 1, 0, 0, -1, -1, -1, -1, -1, -1, -2, -2, 0, 0, -1, -1, 47, 47]
dt7 = [-1, -1, -1, -1, 0, 0, 0, 0, 0, 0, -2, -2, -2, -2, 1, 1, 0, 0, 2, 2, 0, 0, -1, -1, 2, 2, 1, 1, -1, -1, 0, 0]
dt8 = [1, 1, -1, -1, -2, -2, 1, 1, 0, 0, -2, -2, 0, 0, 1, 1, -1, -1, 0, 0, 0, 0, 0, 0, 45, 45, -2, -2, -1, -1, -1, -1]
dt9 = [1, 1, -1, -1, -1, -1, 0, 0, -2, -2, 16, 16, -1, -1, -1, -1, 15, 15, -1, -1, -1, -1, 0, 0, -1, -1, 0, 0, 1, 1, 0, 0]
dt10 = [1, 1, 0, 0, -1, -1, -1, -1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, -1, -1, 1, 1, 1, 1, 0, 0, 0, 0, -17, -17, -19, -19]
dt11 = [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, -1, -1, 0, 0, 2, 2, 1, 1, 2, 2, 1, 1, 0, 0]
dt12 = [1, 1, 3, 3, 1, 1, -1, -1, -1, -1, 0, 0, 0, 0, 0, 0, -1, -1, 0, 0, -1, -1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
dt13 = [-45, -45, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, -1, -1, -1, -1, 1, 1, 1, 1, -1, -1, 1, 1, 1, 1]
dt14 = [0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 3, 3, 0, 0, 4, 4, 3, 3, 1, 1, 1, 1, 1, 1, 1, 1]
dt15 = [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, -45, -45, -2, -2, 2, 2, -1, -1, 0, 0, -1, -1, 1, 1, 4, 4, 0, 0, 2, 2, 1, 1]
dt16 = [0, 0, 0, 0, 0, 0, 1, 1, -1, -1, 1, 1, 0, 0, 1, 1, 2, 2, 1, 1, 1, 1, 0, 0, 3, 3, 1, 1, 1, 1, 0, 0]

# current delays from aavs2.yml (or EDA2)
tpm1 = [0, 0, 7, 7, 0, 0, -3, -3, 1, 1, 4, 4, 1, 1, 0, 0, 3, 3, -1, -1, 4, 4, -2, -2, 4, 4, -1, -1, -1, -1, -1, -1]
tpm2 = [0, 0, 9, 9, 2, 2, -3, -3, 2, 2, 1, 1, 0, 0, 1, 1, 3, 3, -1, -1, -2, -2, -2, -2, 6, 6, 0, 0, 0, 0, 0, 0]
tpm3 = [-37, -37, -40, -40, -39, -39, -36, -36, -37, -37, -36, -36, -38, -38, -40, -40, -34, -34, -36, -36, -39, -39, -38, -38, -38, -38, -37, -37, -37, -37, -38, -38]
tpm4 = [-37, -37, -43, -43, -41, -41, -42, -42, -43, -43, -42, -42, -40, -40, -41, -41, -39, -39, -35, -35, -39, -39, -40, -40, -40, -40, -38, -38, -39, -39, -40, -40]
tpm5 = [9, 9, 5, 5, 2, 2, 11, 11, -16, -16, -17, -17, -21, -21, -17, -17, 1, 1, 3, 3, 1, 1, 3, 3, -18, -18, 5, 5, 4, 4, 3, 3]
tpm6 = [73, 73, 69, 69, 67, 67, 74, 74, 45, 45, 46, 46, 0, 0, 43, 43, 66, 66, 67, 67, 66, 66, 68, 68, 55, 55, 69, 69, 69, 69, 0, 0]
tpm7 = [50, 50, 47, 47, 44, 44, 48, 48, 48, 48, 46, 46, 47, 47, 48, 48, 50, 50, 53, 53, 44, 44, 46, 46, 48, 48, 51, 51, 46, 46, 46, 46]
tpm8 = [48, 48, 47, 47, 47, 47, 44, 44, 45, 45, 46, 46, 46, 46, 44, 44, 52, 52, 46, 46, 45, 45, 45, 45, 0, 0, 50, 50, 47, 47, 49, 49]
tpm9 = [13, 13, 12, 12, 11, 11, 9, 9, 10, 10, 0, 0, 20, 20, 19, 19, -25, -25, 11, 11, 11, 11, 12, 12, 15, 15, 13, 13, 10, 10, 10, 10]
tpm10 = [-15, -15, -19, -19, -19, -19, -20, -20, -17, -17, -20, -20, -19, -19, -17, -17, -17, -17, -18, -18, -22, -22, -21, -21, -18, -18, -16, -16, 0, 0, 0, 0]
tpm11 = [-90, -90, -89, -89, -94, -94, -90, -90, -69, -69, -71, -71, -71, -71, -73, -73, -92, -92, -92, -92, -92, -92, -96, -96, -72, -72, -92, -92, -94, -94, -94, -94]
tpm12 = [-72, -72, -66, -66, -72, -72, -74, -74, -72, -72, -72, -72, -73, -73, -73, -73, -69, -69, -73, -73, -74, -74, -75, -75, -71, -71, -72, -72, -74, -74, -71, -71]
tpm13 = [0, 0, -72, -72, -69, -69, -69, -69, -68, -68, -68, -68, -73, -73, -71, -71, -67, -67, -69, -69, -70, -70, -70, -70, -71, -71, -68, -68, -71, -71, -71, -71]
tpm14 = [-71, -71, -72, -72, -71, -71, -69, -69, -72, -72, -74, -74, -73, -73, -73, -73, -70, -70, -71, -71, -76, -76, -75, -75, -72, -72, -70, -70, -71, -71, -72, -72]
tpm15 = [-68, -68, -73, -73, -71, -71, -69, -69, -72, -72, 0, 0, -70, -70, -70, -70, -69, -69, -68, -68, -71, -71, -73, -73, -69, -69, -68, -68, -71, -71, -71, -71]
tpm16 = [11, 11, 8, 8, 5, 5, 13, 13, 6, 6, 3, 3, 5, 5, 2, 2, 3, 3, 5, 5, 4, 4, 6, 6, 3, 3, 7, 7, 6, 6, 6, 6]    

dt=[]
for i in range(0,17):
   dt.append([])

dt[1]=numpy.array(dt1)
dt[2]=numpy.array(dt2)
dt[3]=numpy.array(dt3)
dt[4]=numpy.array(dt4)
dt[5]=numpy.array(dt5)
dt[6]=numpy.array(dt6)
dt[7]=numpy.array(dt7)
dt[8]=numpy.array(dt8)
dt[9]=numpy.array(dt9)
dt[10]=numpy.array(dt10)
dt[11]=numpy.array(dt11)
dt[12]=numpy.array(dt12)
dt[13]=numpy.array(dt13)
dt[14]=numpy.array(dt14)
dt[15]=numpy.array(dt15)
dt[16]=numpy.array(dt16)

tpm=[]
for i in range(0,17):
   tpm.append([])


tpm[1]=numpy.array(tpm1)
tpm[2]=numpy.array(tpm2)
tpm[3]=numpy.array(tpm3)
tpm[4]=numpy.array(tpm4)
tpm[5]=numpy.array(tpm5)
tpm[6]=numpy.array(tpm6)
tpm[7]=numpy.array(tpm7)
tpm[8]=numpy.array(tpm8)
tpm[9]=numpy.array(tpm9)
tpm[10]=numpy.array(tpm10)
tpm[11]=numpy.array(tpm11)
tpm[12]=numpy.array(tpm12)
tpm[13]=numpy.array(tpm13)
tpm[14]=numpy.array(tpm14)
tpm[15]=numpy.array(tpm15)
tpm[16]=numpy.array(tpm16)


for t in range(1,17):
   tpm[t] = tpm[t] + dt[t]
   
   line = "    - ["
   for a in range(0,32):
      if a < 31 :
         line += ("%d, " % (tpm[t][a]))
      else :
         line += ("%d" % (tpm[t][a]))

         
   
   line += "]"
   
   print "%s" % (line)
   







