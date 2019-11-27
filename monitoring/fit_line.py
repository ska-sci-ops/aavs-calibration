#!/opt/caastro/ext/anaconda/bin/python

# Author : Marcin Sokolowski
# Links :
# http://matplotlib.org/users/pyplot_tutorial.html
# https://python4mpia.github.io/fitting_data/least-squares-fitting.html

# just info :
import sys,os
import math
import numpy
# examples :
# numpy.mean([1,2,3,4,5,6,7,8])
# scipy.stats is a module within a module scipy and has to separately imported :
# version 1 :
# from scipy.stats import pearsonr,linregress 
# version 2 :
from scipy import stats
from matplotlib import pyplot
from optparse import OptionParser,OptionGroup
from pylab import *
import time
# pylab vs pyplot confusion , pylab - sort of python MATLAB 
# applepie - for astro data 

# astropy website :
# from astropy.coordinates import SkyCoord
# import astropy.units as u


# speed of light in m/ps and m/s
C_mps = 0.000299798  #  m/ps
C_ms  = 299798000.00 #  m/s

# MWA global variables :
N_FINE_CHANNELS_PER_COARSE=32 # assuming processing always 24*32 = 762 fine channels 
N_FINE_CHANNELS=768
COARSE_CHANNEL_WIDTH=1.28

# global sqlfile 
sqlfile = None

def mkdir_p(path):
   try:
      os.makedirs(path)
   except OSError as exc: # Python >2.5
      pass
                                 

def parse_options(idx):
   usage="Usage: %prog PHASE_FILE.txt [options]\n"
   usage+='\tFit line to unwrapped phase file PHASE_FILE.txt format - 2 columns Freq[MHz] and Phase[deg]\n'
   parser = OptionParser(usage=usage,version=1.00)
   parser.add_option('-p','--plot',action="store_true",dest="do_plot",default=False, help="Plot data and fit")
   parser.add_option('--hor','--hor_line',action="store_true",dest="fit_hor_line",default=False, help="Fit horizontal line")
   parser.add_option('-i','--iter','--n_iter',dest="n_iter",default=1, help="Number of iteration to remove outliers from the fit",metavar="int",type="int")
   parser.add_option('-m','--max_resid','--limit',dest="limit",default=10, help="Fitting until residuals below this limit",metavar="float",type="float")
   parser.add_option('-o','--outfile','--out',dest="outfile",default=None, help="Name of output file [default %default]")
   parser.add_option('-s','--sqlfile','--sql',dest="sqlfile",default=None, help="Name of output SQL file [default %default]")
   parser.add_option('-c','--comment',dest="comment",default="UNKNOWN", help="Comment to be put in output file [default %default]")
   parser.add_option('--no_png',action="store_false",dest="save_png",default=True, help="Save png file")
   parser.add_option('-a','--amp_dir',dest="amp_dir",default="../amp/", help="Directory where gain txt files are stored [default %default]")
   parser.add_option('--obsid',dest="obsid",default=-1, help="Observations ID for SQL INSERT",metavar="int",type="int")
   parser.add_option('--tileid',dest="tileid",default=-1, help="Tile ID",metavar="int",type="int")
   (options, args) = parser.parse_args(sys.argv[idx:])

   return (options, args)


def read_gains(tile_name,amp_dir,pol) :
   file=amp_dir + "/" + tile_name + "_" + pol + ".txt"
   try :
      gain_table=loadtxt(file)
   
      gain_str=""
      for i in range(0,len(gain_table)) :
         gain_val = gain_table[i][1]
         if len(gain_str)> 0 :
            gain_str += ","
         gain_str += str(gain_val)
      
   
      return gain_str
   except OSError as exc:
      print "ERROR (OSError) : could not read file %s" % file
#      pass
   except :
      print "ERROR (any): could not read file %s" % file
      
   return "-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000,-1000"
   

def read_data(filename) :
   file=open(filename,'r')

   # reads the entire file into a list of strings variable data :
   data=file.readlines()
   # print data

   # initialisation of empty lists :
   x_arr=[]
   y_arr=[]
   min_x=1e20
   max_x=-1e20
   cnt=0
   for line in data : 
      words = line.split(' ')      

      if line[0] == '#' or line[0]=='\n' or len(line) <= 0 or len(words)<2 :
         continue

      if line[0] != "#" :
         x=float(words[0+0])
         y=float(words[1+0])
      
         x_arr.append(x)
         y_arr.append(y)
         cnt += 1
      
         if x > max_x :
            max_x = x
         if x < min_x :
            min_x = x

   print "Frequency range = %.4f - %.4f MHz" % (min_x,max_x)         
   return (x_arr,y_arr,min_x,max_x)

fig_global = None 
   
def fit_line(x_arr, y_arr, save_png=True, do_plot=True, outfile_name=None, limit=20, n_iter=1, comment="UNKNOWN", amp_dir="../amp/" , filename=None,pngfile=None, min_points=2, x_arr_MHz=True, n_ch=10 ):      
   global fig_global
   
   typical_thickness = 3.9
   
   cnt=len(x_arr)
   print "n_iter = %d , cnt = %d" % (n_iter,cnt)
   if len(x_arr) != len(y_arr) :
      print "ERROR : len(x_arr)=%d != len(y_arr)=%d -> cannot continue" % (len(x_arr),len(y_arr))
      return (-10000,-10000)

   if len(x_arr) < min_points :
      print "ERROR : there are only %d points < minimum required %d -> no fit done" % (len(x_arr),min_points)
      return (-10000,-10000)

   min_x = min(x_arr)
   max_x = max(x_arr)   
  
   # copy the original array as it gets overwritten later :
   x_arr_original = x_arr.copy()
   y_arr_original = y_arr.copy()

   # version 1 :
   # slope,intercept, rval, pval, stderr = linregress(x_arr,y_arr)
   # version 2 :
   slope,intercept, rval, pval, stderr = stats.linregress(x_arr,y_arr)
   print "y = {0}*x + {1}".format(slope,intercept)
   # print "rval = {0}".format(rval)
   # print "pval = {0}".format(pval)
   print "stderr = {0}".format(stderr)

   # calculate error from thickness of the data in n_ch bins :
   n_bins = len(x_arr)/n_ch
   thickness_bins = numpy.zeros( n_bins )
   bWarned=False
   for ii in range(0,n_bins) :
      if ii < n_bins :
         thickness_bins[ii] = y_arr[ii*n_ch:(ii+1)*n_ch].std()
         if thickness_bins[ii] <= 0.1 :
            # minimum thicnkess from distribution is ~3.9 deg (see refitting_tests.odt) :
            thickness_bins[ii] = typical_thickness # set to 4 deg 
            if not bWarned :
               print "WARNING : median_thickness <= 0.1 -> setting minimum thickness = 3.9 (bin=%d - printing just once and maybe more)" % (ii)
               bWarned = True

   # Find median thickness :
   median_thickness = numpy.median(thickness_bins)
   if median_thickness <= 0.1 :
      # minimum thicnkess from distribution is ~3.9 deg (see refitting_tests.odt) :
      median_thickness = typical_thickness # set to 4 deg 
      print "WARNING : phase median_thickness <= 0.1 -> setting minimum thickness = 3.9"
   if median_thickness >= 3*typical_thickness :
      min_thickness = numpy.min( thickness_bins )
      print "WARNING : phase median_thickness >= %.2f -> changed to minimum thickness %.2f" % (median_thickness,min(min_thickness,typical_thickness))
      median_thickness = min(min_thickness,typical_thickness)
      
   # Log thickness bins :
   line=""
   for ii in range(0,len(thickness_bins)) :
      line += (" %.2f" % thickness_bins[ii])
   print "%s : Median phase thickness = %.2f from bins : %s" % (filename,median_thickness,line)
   
   # calculate residuals and their standard deviation :
   residuals = numpy.zeros(len(x_arr))
   for ii in range(0,len(x_arr)) :      
      residuals[ii] = ((slope*x_arr[ii]+intercept) - y_arr[ii])
   sigma_resid = residuals.std()
   
   # calculate Chi2/NDOF :
   chi2=0
   for i in range(0,len(x_arr)) :
      model = slope*x_arr[i]+intercept
#      diff = ((y_arr[i] - model) / sigma_resid)
#      # chi2 = chi2 + ((y_arr[i] - model)*(y_arr[i] - model))/math.fabs(model)
      diff = ((y_arr[i] - model) / median_thickness)
      chi2 = chi2 + diff*diff # this gives always 1 - as expected 
   chi2 = chi2 / (len(x_arr)-2) # per degree of freedom

   print "Iter = 0 : PHASE : sigma of residuals = %.2f , median_thickness = %.2f -> chi2/NDOF = %.2f" % (sigma_resid,median_thickness,chi2)
   

   A=slope
   B=intercept
   print "PHASE : Fitted using %d points line y = %.8f x + %.8f" % (cnt,A,B)


   if  n_iter > 1 :
      count=cnt;
      x_val=list(x_arr)
      y_val=list(y_arr)
   
#     print "x_val = %s" % x_val
      max_diff=1e20

      iter=0
      while iter<n_iter and max_diff>limit :
        print
        print "Fitting iteration = %d" % iter
        # find and exclude worst outlier 
        max_i=-1;
        max_diff=-1e20;
        
        for i in range(0,count):
           fit_y = A*x_val[i] + B;
           diff = math.fabs(fit_y - y_val[i]);

           if  diff > max_diff :
              max_diff = diff;
              max_i=i;

        if  max_i >= 0 :
            print "\tPHASE : Maximum residual = %.4f [deg] at %.2f MHz -> excluding this point and re-fitting" %(max_diff,x_val[max_i])

            for i in range(max_i,(count-1)):
               x_val[i] = x_val[i+1]
               y_val[i] = y_val[i+1]

            count = count - 1

        slope,intercept, rval, pval, stderr = stats.linregress(x_val,y_val)
        A = slope;
        B = intercept;
        
        # residuals :
        residuals2 = numpy.zeros(len(x_val))
        for ii in range(0,len(x_val)) : 
           residuals2[ii] = ((slope*x_val[ii]+intercept) - y_val[ii])
        sigma_resid = residuals2.std()
        
        # calculate Chi2/NDOF :
        chi2=0
        for i in range(0,len(x_val)) :
           model = slope*x_val[i]+intercept
           diff = ((y_val[i] - model) / median_thickness)
           chi2 = chi2 + diff*diff # this gives always 1 - as expected 
        chi2 = chi2 / (len(x_val)-2) # per degree of freedom

        print "\tPHASE : Fitted using %d points line y = %.8f x + %.8f -> max_diff=%.2f (vs. limit = %.2f)" % (count,A,B,max_diff,limit)
        print "\tPHASE : Sigma of residuals = %.2f (from %d points), chi2/NDOF = %.2f" % (sigma_resid,len(x_val),chi2)
        
        
        iter = iter + 1

      x_arr=list(x_val)
      y_arr=list(y_val)
   
   # calculation of quality value. It uses original x_arr to include the outlier channels (RFI etc):
   n_bad_channels = 0 
   bad_threshold = 5.00 * median_thickness # using thickness not sigma in threshold (will test if good enough)
   for ii in range(0,len(x_arr_original)) :
      resid = ((slope*x_arr_original[ii]+intercept) - y_arr_original[ii])
      if math.fabs( resid ) > bad_threshold :
         n_bad_channels = n_bad_channels + 1 
         
   n_channels = len(x_arr_original)
   quality_flag = 0 
   if n_channels > 0 :
      quality_flag = ( float(n_channels - n_bad_channels) / float(N_FINE_CHANNELS))
   print "\tPHASE : Number of bad channels = %d / %d -> quality flag = %.4f" % (n_bad_channels,len(x_arr_original),quality_flag)

      
         
   # freq in MHz -> 1/10^6Hz needed !
   A_Hz=A/1e6
   len_m = (A_Hz/360.00)*C_ms
   
   if not x_arr_MHz :
      len_m = A
                     
   fig_idx=0
   if save_png and pngfile is not None :
      print "Saving image ..."
      # generate array of floats of given value :
      # arrays of ZEROS than add 1 :
      # numpy.empty - 
      # x_err=numpy.zeros(count)+1
      # y_err=numpy.zeros(count)+1

      # matplolib.org         
      if fig_global is None :
         fig_global = pyplot.figure(0)

      pyplot.clf()
      fig=fig_global
      # fig = pyplot.figure(fig_idx)
      ax = fig.add_subplot(1,1,1) # create axes within the figure : we have 1 plot in X direction, 1 plot in Y direction and we select plot 1
      ax.plot(x_arr,y_arr,'bo') # nicer circles 
      # ax.plot(x_arr,y_arr,'polar=True') # nicer circles 
      #ax.errorbar(x_arr,y_arr,x_err,y_err,'bo')
      # ax.plot(x_arr,y_arr,'.') # do not connect points with line but plot a point 
      ax.set_xlabel('Frequency [MHz]')
      ax.set_ylabel('Phase [deg]') # r to treat it as raw string 
      
      count_large=numpy.where( fabs(y_arr) > 360 )[0].size
      shift=0      
      if count_large < 20 :
         ax.set_ylim(bottom=-360.00,top=+380.00)
      else :
         print "WARNING : %d values exceeds |360| -> plotting automatic Y-axis range" % (count_large)
         shift=(max(y_arr) - min(y_arr))/10.00
      pyplot.title(filename)
   
      t = numpy.arange(min_x, max_x, 0.1)
      ax.plot(t, A*t+B, 'r--')
  
      minx=min(x_arr)
      maxx=max(x_arr)    
      miny=min(y_arr)
      maxy=max(y_arr)    
       
      desc="Fitted delay = %.2f [m] , intercept = %.2f [deg]" % (len_m,B)
      # plt.text(minx, maxy-(maxy-miny)*0.05, desc, fontsize=18)
      plt.text(minx, 350.00, desc, fontsize=15)
      
      desc2="Stderr = %.2f, sigma_resid = %.2f, chi2/ndof = %.2f" % (stderr,sigma_resid,chi2)
      plt.text(minx, 310.00-shift, desc2, fontsize=15)

      desc3="Thickness = %.2f, N_bad_ch = %d , quality = %.4f" % (median_thickness,n_bad_channels,quality_flag)
      plt.text(minx, 275.00-2*shift, desc3, fontsize=15)
    
      print "Saving file %s" % (pngfile)
      mkdir_p("images/")
      if pngfile.find("images/")<0 :
         pngfile="images/" + pngfile
      pyplot.savefig(pngfile)   
      pyplot.pause(0.025)


# WARNING : plotting happens anyway - even when do_plot=False -> not sure why, but I commented this part below :     
#      if do_plot :       
#         print "pyplot.show"
         # pyplot.show()        
         # pyplot.show(block=False)
#         pyplot.pause(0.025)
         # time.sleep(1)
         # pyplot.close()
      print "done"
      
      
      # close(fig)
      # pyplot.close()
      fig_idx = fig_idx + 1 


   outfile=None
   if outfile_name is not None and sqlfile is not None :
      print "Saving output files %s and %s ..." % (outfile_name,sqlfile)
      outfile=open(outfile_name,"w") # was a+ in 2pols version 
      # sqlfile_f=open(sqlfile,"w")         

      len_comment=len(comment)
      tile_name=comment[4:4+len_comment-6]
      pol=comment[len_comment-1:]
      gains=read_gains(tile_name,amp_dir,pol)

      # outline = "%s %s %.8f %.8f %.8f %s\n" % (tile_name,pol,A/1e6,B,len_m,gains)
      # outfile.write(outline)

      # outline = "INSERT INTO CalSolutions (obsid,cal_tileid,cal_pol,cal_delay_m,cal_intercept,cal_gains) VALUES (%d,%d,'%s',%.8f,%.8f,ARRAY[%s]);\n" % (obsid,tileid,pol,len_m,B,gains)
      outline = "%.8f,%.8f,ARRAY[%s]" % (len_m,B,gains)
      outfile.write(outline)

      outfile.close()
      # sqlfile_f.close()
      print "done"

   return (len_m,B,sigma_resid,chi2,quality_flag)

def fit_hor_line(x_arr, y_arr, save_png=True, do_plot=True, outfile_name=None, limit=20, n_iter=1, comment="UNKNOWN", amp_dir="../amp/" , filename=None,pngfile=None, min_points=1, limit_in_sigma=5 ):      
   print "n_iter = %d" % (n_iter)
   cnt=len(x_arr)
   if len(x_arr) != len(y_arr) :
      print "ERROR : len(x_arr)=%d != len(y_arr)=%d -> cannot continue" % (len(x_arr),len(y_arr))
      return (-10000,-10000)

   if len(x_arr) < min_points :
      print "ERROR : there are only %d points < minimum required %d -> no fit done" % (len(x_arr),min_points)
      return (-10000,-10000)

   min_x = min(x_arr)
   max_x = max(x_arr)   
   
   for i in range(0,len(x_arr)):
      print "%d (%.2f,%.2f)" % (i,x_arr[i],y_arr[i])
  

   # version 1 :
   # slope,intercept, rval, pval, stderr = linregress(x_arr,y_arr)
   # version 2 :
   z = numpy.polyfit( x_arr , y_arr, 0  )
   slope=0
   intercept=z[0]
   diff = y_arr - z[0]
   stderr = numpy.std( diff, 0 )
   rval = 0
   pval = 0
   print "y = {0}*x + {1}".format(slope,intercept)
   # print "rval = {0}".format(rval)
   # print "pval = {0}".format(pval)
   print "stderr = {0}".format(stderr)

   A=slope
   B=intercept
   print "Fitted using %d points line y = %.8f x + %.8f" % (cnt,A,B)


   if  n_iter > 1 :
      count=cnt;
      x_val=list(x_arr)
      y_val=list(y_arr)
   
#     print "x_val = %s" % x_val
      max_diff=1e20

      if limit_in_sigma > 0 :
         limit=limit_in_sigma*stderr

      iter=0
      while iter<n_iter and max_diff>limit :
        print
        print "Fitting iteration = %d" % iter
        # find and exclude worst outlier 
        max_i=-1;
        max_diff=-1e20;
        
        for i in range(0,count):
           fit_y = A*x_val[i] + B;
           diff = math.fabs(fit_y - y_val[i]);

           if  diff > max_diff :
              max_diff = diff;
              max_i=i;

        if  max_i >= 0 :
            print "Maximum residual = %.4f [deg] at %.2f MHz -> excluding this point and re-fitting" %(max_diff,x_val[max_i])

            for i in range(max_i,(count-1)):
               x_val[i] = x_val[i+1]
               y_val[i] = y_val[i+1]

            count = count - 1

#        slope,intercept, rval, pval, stderr = stats.linregress(x_val,y_val)
        z = numpy.polyfit( x_arr , y_arr, 0  )
        slope=0
        intercept=z[0]
        diff = y_arr - z[0]
        stderr = numpy.std( diff, 0 )
        rval = 0
        pval = 0

        A = slope;
        B = intercept;
        print "Fitted using %d points line y = %.8f x + %.8f -> max_diff=%.2f (vs. limit = %.2f)" % (count,A,B,max_diff,limit)
        print "Stderr = %.2f" % (stderr)
        
        iter = iter + 1
        
        if limit_in_sigma > 0 :
           limit=limit_in_sigma*stderr
           print "Limit %.2f sigma = %.2f" % (limit_in_sigma,limit)

      x_arr=list(x_val)
      y_arr=list(y_val)
         
         
   if save_png and pngfile is not None :
      # matplolib.org         
      fig=pyplot.figure()
      ax = fig.add_subplot(1,1,1) # create axes within the figure : we have 1 plot in X direction, 1 plot in Y direction and we select plot 1
      ax.plot(x_arr,y_arr,'bo') # nicer circles 
      # ax.plot(x_arr,y_arr,'polar=True') # nicer circles 
      #ax.errorbar(x_arr,y_arr,x_err,y_err,'bo')
      # ax.plot(x_arr,y_arr,'.') # do not connect points with line but plot a point 
      ax.set_xlabel('Unixtime')
      ax.set_ylabel('Slope [m]') # r to treat it as raw string 
   
      t = numpy.arange(min_x, max_x, 0.1)
#     print t
      ax.plot(t, A*t+B, 'r--')
      pyplot.title(filename)
  
      minx=min(x_arr)
      maxx=max(x_arr)    
      miny=min(y_arr)
      maxy=max(y_arr)    
       
      desc="Fitted = %.2f [deg]" % (B)
      plt.text(minx, maxy-(maxy-miny)*0.05, desc, fontsize=18)
    
      mkdir_p("images/")
      pngfile="images/" + pngfile
      pyplot.savefig(pngfile)   
     
      if do_plot :       
         pyplot.show()        


   outfile=None
   if outfile_name is not None :
      outfile=open(outfile_name,"w") # was a+ in 2pols version 
      # sqlfile_f=open(sqlfile,"w")         

      len_comment=len(comment)
      tile_name=comment[4:4+len_comment-6]
      pol=comment[len_comment-1:]
      gains=read_gains(tile_name,amp_dir,pol)

      # outline = "%s %s %.8f %.8f %.8f %s\n" % (tile_name,pol,A/1e6,B,len_m,gains)
      # outfile.write(outline)

      # outline = "INSERT INTO CalSolutions (obsid,cal_tileid,cal_pol,cal_delay_m,cal_intercept,cal_gains) VALUES (%d,%d,'%s',%.8f,%.8f,ARRAY[%s]);\n" % (obsid,tileid,pol,len_m,B,gains)
      outline = "%.8f,%.8f,ARRAY[%s]" % (len_m,B,gains)
      outfile.write(outline)

      outfile.close()
      # sqlfile_f.close()

   return (B)



def main() :
   filename="data.txt"
   if len(sys.argv) > 1:
      filename = sys.argv[1]
   
   (options, args) = parse_options(1)   
   sqlfile=options.outfile
   pngfile=filename.replace('.txt', '.png' )

#   sqlfile=sqlfile.replace('.txt', '.sql')
#   if options.sqlfile is not None :
#      sqlfile=options.sqlfile

   print "Processing file = %s" % (filename)     
   (x_arr,y_arr,min_x,max_x) = read_data(filename)  
   x_arr=np.array(x_arr)
   y_arr=np.array(y_arr)
   
   if options.fit_hor_line :
      (B) = fit_hor_line(x_arr,y_arr,save_png=options.save_png,do_plot=options.do_plot,outfile_name=options.outfile,limit=options.limit,n_iter=options.n_iter,comment=options.comment,amp_dir=options.amp_dir,filename=filename,pngfile=pngfile)
      print "Fitted value = %.2f [deg]" % (B)
   else :
      (len_m,B) = fit_line(x_arr,y_arr,save_png=options.save_png,do_plot=options.do_plot,outfile_name=options.outfile,limit=options.limit,n_iter=options.n_iter,comment=options.comment,amp_dir=options.amp_dir,filename=filename,pngfile=pngfile)         
      print "delay = %.2f [m] , intercept = %.2f [deg]" % (len_m,B)
  
if __name__ == "__main__":
   main()
  
