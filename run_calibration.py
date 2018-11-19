from datetime import datetime
from datetime import timedelta
from glob import glob
import os,sys,getopt
import subprocess
import numpy as np
import psycopg2
import time
import pytz
import fit_phase_delay

nyquist_freq = 400.0	# MHz
nof_antennas = 256
nof_channels = 512
start_channel = 64
code_version="""run_calibration_v1"""
username=os.getenv('USER')
dump_time = 1.9818086		# Correlation matrix dump time (seconds)

def generate_header(channel, integration_time):
    string = """FIELDNAME drift_aavs1
TELESCOPE AAVS1   # telescope name like MWA, MOST, ATCA etc
N_SCANS   1     # number of scans (time instants) in correlation products
N_INPUTS  512    # number of inputs into the correlation products
N_CHANS   1   # number of channels in spectrum
CORRTYPE  B     # correlation type to use. 'C'(cross), 'B'(both), or 'A'(auto)
INT_TIME  {0}   # integration time of scan in seconds
FREQCENT  {1} # observing center freq in MHz
BANDWIDTH 0.78125  # total bandwidth in MHz
HA_HRS    -0.00833333  # the HA at the *start* of the scan. (hours)
DEC_DEGS  -26.7033 # the DEC of the desired phase centre (degs)
INVERT_FREQ 0   # 1 if the freq decreases with channel number
CONJUGATE 1     # conjugate the raw data to fix sign convention problem if necessary
GEOM_CORRECT 1  # apply geometric phase corrections when 1. Don't when 0 """

    string = string.format(integration_time, channel * (nyquist_freq / nof_channels))

    return string

def read_gain_solution_file(filepath):
    """ Read coefficients from filepath """

    # Read file content. First lines contains header, so can be ignored
    with open(filepath, 'r') as f:
        content = f.readlines()

    # Each line contains an index, the time and the coefficient for each antenna
    entries = [value for value in content[0].split(' ') if value.strip() != '']
    entries = [float(x) for x in entries[2:]]
    
    # Return values
    return entries

def load_coefficients(directory, channel):
    # Load coefficient files for given file prefix
    xx_amp, xx_phase, yy_amp, yy_phase = None, None, None, None
    for f in glob("{}*.txt".format(os.path.join(directory, "chan_{}_selfcal".format(channel)))):
        if 'XX' in f and 'amp' in f:
            xx_amp = read_gain_solution_file(f)
        elif 'XX' in f and 'pha' in f:
            xx_phase = read_gain_solution_file(f)
        elif 'YY' in f and 'amp' in f:
            yy_amp = read_gain_solution_file(f)
        elif 'YY' in f and 'pha' in f:
            yy_phase = read_gain_solution_file(f)
        else:
            logging.warning("{} has an invalid filename format".format(f))

    # All files loaded, check that we have all required coefficients
    if not all([xx_amp, xx_phase, yy_amp, yy_phase]):
        logging.warn("Missing files in specified directory ({})".format(directory))
        exit()

    # Return values
    return xx_amp, xx_phase, yy_amp, yy_phase

def print_usage():
  """Print a usage message and exit
  """
  sys.stderr.write("Usage:\n")
  sys.stderr.write(sys.argv[0]+ " [options]\n")
  sys.stderr.write("\t-D data_dir\tdirectory to work in, where the data are\n")
  sys.stderr.write("\t-C\t\tskip the calibration step (useful if there are already solutions)\n")
  sys.exit(1)

# main program

# Directory where correlation matrices are stored
data_directory = "."
cal_skip=False

optstring="D:C"
try:
  opts, args = getopt.getopt(sys.argv[1:], optstring)
except:
  print_usage()
for o, a in opts:
    if o == "-D":
        data_directory = a
    elif o in ("-C"):
	cal_skip=True
    else:
        assert False,"unhandled option"+ o+"\n"

# Integrations over which to integrate
nof_integrations = 1

# Channel to calibrate
t0 = time.time()
xx_amp = np.zeros((nof_channels, nof_antennas))
xx_phase = np.zeros((nof_channels, nof_antennas))
yy_amp = np.zeros((nof_channels, nof_antennas))
yy_phase = np.zeros((nof_channels, nof_antennas))
x_delay = np.zeros((2,nof_antennas))
y_delay = np.zeros((2,nof_antennas))

if cal_skip is False:
  for channel in range(start_channel, nof_channels):
    print("Processing channel {}".format(channel))

    # Generate header
#    with open(os.path.join(data_directory, "header.txt"), "w") as f:
#        f.write(generate_header(channel, dump_time * nof_integrations))

    cal_script = "calibration_script.sh"	# this should be in PATH
    subprocess.check_call([cal_script,"-D",data_directory,"-T",str(dump_time), "-N",str(nof_integrations), str(channel)])

for channel in range(start_channel, nof_channels):
  # At this point calibration solutions should be ready, read files and save locally
  try:
    x_amp, x_pha, y_amp, y_pha = load_coefficients(data_directory, channel)
    xx_amp[channel, :] = x_amp
    xx_phase[channel, :] = x_pha
    yy_amp[channel, :] = y_amp
    yy_phase[channel, :] = y_pha
  except:
    print "Unable to load data for channel "+str(channel)

t1 = time.time()

# now fit a delay to each pol of each antenna
for a in range(nof_antennas):
  print 'Solving delays for ant '+str(a)
  delay_model_x = fit_phase_delay.fitDelay(fit_phase_delay.zeroBadFreqs(np.copy(xx_phase[:,a])))
  delay_model_y = fit_phase_delay.fitDelay(fit_phase_delay.zeroBadFreqs(np.copy(yy_phase[:,a])))
  if delay_model_x is None or delay_model_y is None:
    print "No solution for this antenna"
  else:
    x_delay[:,a] = delay_model_x
    y_delay[:,a] = delay_model_y
    print "Ph0/Delay x: %f,%f, y: %f,%f" % (delay_model_x[0],delay_model_x[1],delay_model_y[0],delay_model_y[1])

# Calibrated all channels of interest
print "Processed in {}".format(t1-t0)

# Create connection to the calibration database.
#Do not have to use password here since DB is set up to recognise aavs user
conn = psycopg2.connect(database='aavs')
cur = conn.cursor()

# Create solution
# the local time for the dump is encoded in the directory name for now
if data_directory != '.':
  currdir=os.path.split(data_directory)[-1]
else:
  currdir=os.path.split(os.getcwd())[-1] # the local time for the dump is encoded in the directory name for now
fit_time = datetime.strptime(currdir,"%Y_%m_%d-%H:%M") -timedelta(hours=8)
print 'Creating solutions for fit_time '+str(fit_time)
create_time = datetime.utcnow()
cur.execute("""set timezone='UTC'""") # Just do everything in UTC to avoid problems
cur.execute('''INSERT INTO calibration_fit(create_time, fit_time, creator, code_version)
               VALUES (%s, %s, %s, %s)''', (create_time,fit_time,username,code_version) )

# Create calibration solutions for each antenna
for antenna in range(nof_antennas):
    x_amp = '{{{}}}'.format(', '.join([str(i) for i in xx_amp[:, antenna]]))
    x_pha = '{{{}}}'.format(', '.join([str(i) for i in xx_phase[:, antenna]]))
    y_amp = '{{{}}}'.format(', '.join([str(i) for i in yy_amp[:, antenna]]))
    y_pha = '{{{}}}'.format(', '.join([str(i) for i in yy_phase[:, antenna]]))

#    cur.execute('''INSERT INTO calibration_solution(fit_time, create_time, ant_id, x_amp, y_amp, x_pha, y_pha)
#                   VALUES ('{}', '{}', {}, '{}', '{}', '{}','{}')'''.format(fit_time, create_time, antenna, x_amp, 
#                                                                            y_amp, x_pha, y_pha))
    q = '''INSERT INTO calibration_solution(fit_time, create_time, ant_id, x_amp, y_amp, x_pha, y_pha,x_delay,x_phase0,y_delay,y_phase0)
	VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '''
    cur.execute(q,(fit_time, create_time, antenna, x_amp, y_amp, x_pha, y_pha,x_delay[1,antenna],x_delay[0,antenna],y_delay[1,antenna],y_delay[0,antenna])) 

# Commit and close connection
conn.commit()
conn.close()
