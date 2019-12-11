# Script by Randall Wayth to plot calibration solutions with fits overplotted (requires access to database)
# TODO : make it a bit more "parameterised"

# quick and dirty script to plot cal solutions from database, corresponding to a particular time
# the default plan uses the directory name as the time the data were taken based on Alessio's script
import psycopg2,os,numpy,sys
import matplotlib
if not 'matplotlib.backends' in sys.modules:
   matplotlib.use('agg') # not to use X11
import matplotlib.pyplot as plt   
from datetime import datetime
from datetime import timedelta
import pytz
from optparse import OptionParser,OptionGroup

def do_plots( station_id ): 
   conn = psycopg2.connect("dbname='aavs'")

   cur = conn.cursor()

   # set the time of the cal. Find the nearest entry in the calibration_fit table to the desired time
   # and the most recent entry for that time
   #target_fittime="2018_09_16-10:00"
   currdir=os.path.split(os.getcwd())[-1] # the local time for the dump is encoded in the directory name for now
   mytz=pytz.timezone('Australia/West')
   target=mytz.localize(datetime.strptime(currdir,"%Y_%m_%d-%H:%M"))
   query="select fit_time from calibration_solutions where station_id=%d order by abs(extract(epoch from (fit_time - %s))) limit 1"
   print("Query is: %s. Date is: %s" % (query,str(target)))
   cur.execute(query,(station_id,target,))

   rows = cur.fetchall()
   fit_time = rows[0][0] 

   # now fetch the most recent solution for this time
   query="select create_time from calibration_solutions where fit_time=%s and station_id=%d order by create_time desc limit 1"
   cur.execute(query,(fit_time,station_id,))

   rows = cur.fetchall()
   create_time = rows[0][0]

   cchan_freqs=numpy.arange(512)*400./512. # channel central freqs in MHz
   # do not plot some freqs
   cchan_flag = numpy.copy(cchan_freqs)
   cchan_flag[0:127]=0	# do not plot below 100 MHz
   cchan_flag[310:364]=0	# do not plot the satellite freqs
   cchan_flag[440:486]=0  # do not plot the mystery RFI above 350 MHz
   c_ind = numpy.nonzero(cchan_flag)

   # divide antennas into groups of 16 and plot phases for each group
   fig,ax = plt.subplots(4,4, sharex='all', sharey='all',figsize=[10,7.5])
   fig.subplots_adjust(left=0.05, bottom=0.07, right=0.98, top=0.95, wspace=0.2, hspace=0.3)
   ax1d=ax.flatten()
   for group in range(16):
     print "Processing group "+str(group)
     # make a new plot
     for subgroup_ind in range(16):
       ant_ind = group*16 + subgroup_ind
       ax1d[subgroup_ind].set_ylim([-200,200])
       ax1d[subgroup_ind].set_title('Ant '+str(ant_ind+1))
       qu_cal="select x_pha,y_pha,x_amp,y_amp,x_delay,y_delay,x_phase0,y_phase0 from calibration_solution where fit_time = %s and create_time = %s and ant_id = %s and station_id = %d"
       cur.execute(qu_cal,(fit_time,create_time, ant_ind, station_id))
       allcals=cur.fetchall()
       assert (len(allcals) == 1)
       #
       x_pha = numpy.array(allcals[0][0])
       y_pha = numpy.array(allcals[0][1])
       x_amp = allcals[0][2]
       y_amp = allcals[0][3]
       x_del = allcals[0][4]
       y_del = allcals[0][5]
       x_ph0 = allcals[0][6]
       y_ph0 = allcals[0][7]
       # make model data
       if x_del is not None and y_del is not None and x_ph0 is not None and y_ph0 is not None:
         model_ph_x = (2*numpy.pi*x_del*cchan_freqs + x_ph0)
         model_ph_y = (2*numpy.pi*y_del*cchan_freqs + y_ph0)
       # limit phases to between -pi and pi
       model_ph_x_deg = numpy.arctan2(numpy.sin(model_ph_x),numpy.cos(model_ph_x))*180/numpy.pi
       model_ph_y_deg = numpy.arctan2(numpy.sin(model_ph_y),numpy.cos(model_ph_y))*180/numpy.pi
       # plot the data
       ax1d[subgroup_ind].plot(cchan_freqs[c_ind], x_pha[c_ind],'1')
       ax1d[subgroup_ind].plot(cchan_freqs[c_ind], y_pha[c_ind],'x')
       #plot the models
       if x_del is not None and x_del is not None and x_ph0 is not None and y_ph0 is not None:
         ax1d[subgroup_ind].plot(cchan_freqs, model_ph_x_deg,':')
         ax1d[subgroup_ind].plot(cchan_freqs, model_ph_y_deg,'--')
       #
     fig.savefig("cal_phase_"+str(group)+".png")
     for subgroup_ind in range(16):
        ax1d[subgroup_ind].clear()


def parse_options(idx=0):
   usage="Usage: %prog [options]\n"
   usage+='\tPlots visibilities for given tile and all other tiles\n'
   parser = OptionParser(usage=usage,version=1.00)
   parser.add_option("--station_id", '--station', dest="station_id", default=2, help="Station ID (as in the station configuratio file) [default: %]", type=int )
   

   (options, args) = parser.parse_args(sys.argv[idx:])

   return (options, args)


if __name__ == "__main__":
   (options, args) = parse_options()
   do_plots( station_id = options.station_id )
   
   