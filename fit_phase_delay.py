from scipy.optimize import least_squares
import os,sys,getopt
import numpy as np
import logging

nyquist_freq = 400.0	# MHz
nof_antennas = 256
nof_channels = 512
start_channel = 64
code_version="""fit_phase_delay_v1"""
username=os.getenv('USER')
logging.basicConfig()
logger = logging.getLogger(__name__)

def zeroBadFreqs(phases):
  """set phases on known bad frequencies to zero so that they are not used in the solution
  """
  # below 50 MHz
  phases[0:64] *= 0.0
  # below 110 MHz, because there is typically low SNR in this range
  phases[0:140] *= 0.0
  # Orbcomm
  phases[176:178] *= 0.0
  # satellites @ 240-280:
  phases[308:360] *= 0.0
  # unkown things 360-380 MHz
  phases[461:487] *= 0.0
  return phases

def modelFuncPhase(params,x):
  """model function with parameters
  ph0: radian
  delay: (microsec)
  Phase diff = 2*pi*freq*delay
  where freq and delay should be in equivalent units, like MHz and microsec
  """
  d_nu = (nyquist_freq / nof_channels) # spacing of frequency points
  #print "x: "+str(x)
  #print "params: "+str(params)
  model = params[0] + 2*np.pi*x*d_nu*params[1]
  model_c = np.cos(model)+ 1.0j*np.sin(model)
  #print "model: "+str(model)
  return model_c

def fitFuncPhase(params,x,y):
  """function to return the pentaly or distance between model and data
  Both model and data are normalised complex numbers, so the difference in phase can be computed
  by multiplying one with the conj of the other. This is safe for the case of phase wraps etc.
  params: the model fits params [ph0,delay]
  x: vector of x values for the data
  y: vector of y measured data values
  Assumes data and model are unit magnitude complex numbers
  """
  #print "Y: "+str(y)
  return np.angle(y * np.conj(modelFuncPhase(params,x)))

def fitDelay(phases):
  """Fit a model to the phase behaviour of the bandpass consisting of two parameters:
  1- a channel-0 phase
  2- a delay term that translates to linear phase slope
  """
  # find first non-zero element of array and use that for initial ch0 estimate
  nonzeros = np.nonzero(phases)
  if len(nonzeros[0])==0:
    # there are no non-zero gain entries, nothing to do here. Return null model
    return None
  xs = nonzeros[0]
  ys = np.cos(phases[xs]*np.pi/180)+1j*np.sin(phases[xs]*np.pi/180)   # use normalised complex numbers for the phases
  # do initial brute-force search of parameter space
  delay_grid=np.linspace(-0.05,0.05,200)
  sols0 = np.array([np.sum(fitFuncPhase((0.0, s), xs, ys)**2) for s in delay_grid]) # sol with 0 phase
  sols180 = np.array([np.sum(fitFuncPhase((np.pi, s), xs, ys)**2) for s in delay_grid]) # sol with 180 phase
  best_0 = np.argmin(sols0)
  best_180 = np.argmin(sols180)
  logger.debug('Best sol for 0 phase: %f, best for 180 phase :%f' % (sols0[best_0],sols180[best_180]))
  if sols0[best_0] < sols180[best_180]:
    init_delay = delay_grid[np.argmin(sols0)]
    ch0_phase=0.0
  else:
    init_delay = delay_grid[np.argmin(sols180)]
    ch0_phase=np.pi
  # use best solution from brute-force as init guess for iterative solution
  x0 = np.array([ch0_phase, init_delay])
  #print 'Init guess: '+str(x0)
  res_lsq = least_squares(fitFuncPhase, x0, args=(xs, ys),loss='soft_l1',x_scale=[0.001,0.1],jac='3-point',diff_step=np.array([0.01,0.001]))
  logger.info('Ph result: '+str(res_lsq.cost)+'. Status: '+str(res_lsq.status)+'. params: '+str(res_lsq.x)+'. nfev: '+str(res_lsq.nfev)+'. Reason: '+res_lsq.message)
  return res_lsq.x

# main program
if __name__ == "__main__":
  logger.setLevel(logging.DEBUG)
  ph1=np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,134.094,-178.121,0,131.658,63.401,73.043,122.247,50.426,44.698,53.786,46.017,31.693,31.656,34.384,35.096,16.695,16.697,20.23,26.91,82.88,71.989,71.99,67.53,54.727,57.291,56.526,56.356,40.676,43.399,43.955,43.696,36.995,37.896,39.341,40.14,40.914,42.119,43.566,44.765,47.179,48.657,50.53,52.323,49.909,49.91,51.302,53.736,61.738,63.676,63.678,65.45,68.481,70.052,70.054,71.871,50.787,52.381,54.191,53.737,37.687,39.218,40.73,40.191,34.416,35.779,37.258,39.182,57.016,58.691,60.34,62.113,69.118,70.826,72.246,73.57,68.641,68.643,70.126,71.465,63.333,63.335,65.238,66.733,64.839,66.366,66.376,68.143,64.403,65.995,67.575,67.54,64.72,66.401,67.987,67.718,59.576,61.577,63.168,64.941,73.76,75.351,76.942,78.338,75.351,76.93,78.666,80.318,80.509,80.511,82.127,85.126,148.801,150.395,150.397,152.047,91.688,93.367,93.369,95.167,107.311,108.888,110.49,110.311,101.125,102.677,104.223,103.998,87.249,88.839,90.47,91.42,69.763,71.351,72.901,74.383,69.451,71.022,72.611,74.347,83.074,83.077,84.668,86.342,94.527,94.529,96.076,97.686,102.649,104.209,104.211,105.815,104.266,105.857,107.449,107.329,105.248,106.839,108.431,108.198,98.932,100.541,102.127,103.6,99.992,101.584,103.212,104.742,104.251,105.843,107.465,109.166,111.426,111.429,113.021,114.689,119.279,120.871,120.874,122.384,119.682,121.266,121.269,122.731,118.733,120.337,121.929,121.832,121.242,122.828,124.421,124.268,119.069,120.66,122.256,123.734,117.835,119.422,121.014,122.416,115.775,117.367,118.96,120.446,115.858,115.861,117.446,118.968,118.135,118.138,119.78,121.366,124.79,126.383,126.386,128.06,132.261,133.854,135.455,135.405,134.716,136.309,137.902,137.728,131.644,133.247,134.84,136.309,130.128,131.722,133.315,134.843,131.842,133.447,135.06,136.54,134.608,134.611,136.205,137.779,140.271,141.864,141.868,143.533,144.838,146.431,146.434,36.245,38.583,40.176,41.771,41.776,144.588,146.182,147.796,42.661,33.182,34.781,36.379,38.003,-91.764,-90.171,-88.577,-86.809,-174.875,-173.279,-171.685,-170.09,16.575,16.578,18.172,20.255,-106.596,-106.593,-104.999,-103.354,-96.309,-94.722,-94.719,-93.129,-125.233,-123.638,-122.038,-122.044,148.812,150.406,152,151.861,148.621,150.229,151.804,152.776,5.285,6.912,8.504,10.134,151.448,153.041,154.635,156.438,173.264,173.268,174.906,175.413,165.307,166.901,166.905,168.508,170.951,172.545,172.547,174.164,175.044,176.639,178.233,178.13,176.461,178.055,179.649,179.611,179.484,-178.922,-177.327,-175.792,-178.872,-177.277,-175.683,-174.192,-177.389,-175.794,-174.2,-172.601,-171.754,-171.751,-170.156,-168.652,-170.127,-170.123,-168.528,-166.993,-168.339,-166.744,-166.74,-165.344,-172.69,-171.095,-169.5,-169.534,-171.185,-169.59,-167.995,-168.102,-169.333,-167.738,-166.143,-164.73,-172.184,-170.589,-168.994,-167.593,-175.873,-174.278,-172.683,-171.103,-172.054,-172.053,-170.458,-168.903,-167.75,-166.155,-166.152,-164.528,-162.005,-160.41,-160.406,-158.903,-167.049,-165.454,-163.859,-163.834,-154.014,-152.419,-150.824,-151.228,-171.7,-170.105,-168.51,-166.962,-151.6,-150.005,-148.41,-146.935,-152.622,-151.027,-149.432,-148.005,-154.689,-154.686,-153.091,-145.309,6.51,6.513,8.108,9.741,2.471,4.066,4.07,5.982,4.539,6.134,7.729,7.976,12.565,14.16,15.755,15.763,-133.93,-132.33,-130.72,-128.022,47.289,48.884,50.479,52.085,-138.633,-137.038,-135.443,-133.929,-135.903,-135.9,-134.304,-132.758,-135.433,-133.838,-133.834,-132.326,-134.702,-133.107,-133.103,-131.585,-133.784,-132.189,-130.594,-130.679,-134.957,-133.362,-131.765,-131.762,-130.167])

  ph2=np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,108.678,137.854,0,36.84,19.492,-17.674,19.756,87.366,108.141,103.32,95.174,108.065,108.151,102.36,108.46,92.974,92.939,89.199,87.793,-176.8,160.509,160.472,142.1,127.368,122.535,115.04,115.473,137.149,131.91,123.873,124.074,136.502,129.864,124.465,117.788,148.497,142.11,136.572,131.384,159.334,153.7,146.669,140.126,157.444,157.397,151.426,146.3,-176.319,177.527,177.478,172.804,-179.561,173.692,173.642,168.475,175.548,169.406,163.332,163.529,169.953,163.441,157.271,157.408,170.652,164.453,158.288,152.624,-169.774,-175.951,177.851,172.442,-149.368,-155.571,-161.759,-167.488,-152.096,-152.157,-158.347,-164.224,-150.603,-150.666,-156.861,-162.492,-148.73,-154.954,-155.011,-160.558,-151.856,-158.065,-164.311,-164.235,-158.255,-164.557,-170.79,-170.474,-152.062,-157.941,-164.189,-169.658,-132.528,-138.766,-145.004,-150.656,-123.086,-129.452,-135.392,-140.973,-98.342,-98.416,-104.668,-111.313,-145.051,-151.309,-151.385,-157.731,-95.141,-101.399,-101.476,-107.111,-77.734,-84.102,-90.335,-90.116,-80.36,-86.544,-92.769,-92.321,-75.057,-81.328,-87.611,-93.658,-79.954,-86.228,-92.55,-98.14,-65.133,-71.449,-77.728,-83.173,-61.585,-61.672,-67.953,-73.602,-51.877,-51.922,-58.356,-64.035,-45.946,-52.266,-52.357,-58.307,-49.094,-55.351,-61.645,-61.221,-42.415,-48.782,-55.089,-54.777,-42.664,-48.954,-55.261,-61.176,-39.717,-46.02,-52.325,-58.083,-29.516,-35.824,-42.087,-47.635,-25.194,-25.294,-31.606,-37.301,-13.191,-19.486,-19.588,-25.293,-7.814,-14.141,-14.245,-20.167,-3.987,-10.327,-16.651,-16.04,7.816,1.484,-4.843,-4.367,15.537,9.22,2.89,-2.938,19.499,13.166,6.83,1.078,23.948,17.611,11.272,5.401,16.388,16.275,9.933,4.004,20.664,20.549,14.203,8.478,33.99,27.642,27.525,21.958,48.55,42.197,35.852,36.352,55.812,49.455,43.098,43.544,64.005,57.655,51.294,45.467,68.404,62.04,55.675,49.77,73.629,67.252,60.883,55.005,72.331,72.206,65.833,59.954,79.857,73.481,73.354,67.435,81.109,74.73,74.601,-123.701,-130.204,-136.585,-142.969,-143.092,93.865,87.479,81.092,137.233,130.98,124.589,118.2,111.831,37.283,30.89,24.495,18.566,129.089,122.695,116.297,109.904,22.359,22.22,15.819,9.202,49.564,49.424,43.018,36.896,58.328,51.955,51.812,45.27,-93.263,-99.694,-106.104,-106.276,132.962,126.546,120.13,120.698,142.532,136.127,129.687,123.643,-122.166,-128.587,-135.012,-141.415,159.943,153.519,147.086,141.388,167.341,167.191,160.761,154.032,166.183,159.75,159.597,153.898,179.89,173.452,173.375,167.508,-174.361,179.198,172.757,173.077,-171.322,-177.766,175.788,176.214,-165.232,-171.68,-178.129,175.835,-165,-171.451,-177.904,176.036,-162.291,-168.746,-175.203,178.807,-161.566,-161.729,-168.189,-174.08,-151.629,-151.793,-158.257,-164.189,-144.069,-150.536,-150.701,-156.7,-139.357,-145.827,-152.297,-151.844,-130.943,-137.416,-143.891,-143.586,-126.861,-133.338,-139.816,-145.852,-122.557,-129.037,-135.519,-141.444,-116.658,-123.142,-129.627,-135.484,-115.98,-116.068,-122.556,-128.389,-106.09,-112.581,-112.758,-118.685,-99.848,-106.342,-106.52,-112.249,-6.384,-12.872,-19.369,-19.848,-89.414,-95.915,-102.432,-101.777,12.36,5.854,-0.651,-7.225,-72.54,-79.049,-85.556,-91.494,-69.639,-76.151,-82.663,-88.744,-74.079,-74.266,-80.782,-87.818,-45.254,-45.441,-51.961,-58.266,-50.603,-57.126,-57.315,-62.764,-43.793,-50.319,-56.847,-56.178,-16.407,-22.936,-29.467,-29.634,-42.654,-49.183,-55.709,-63.827,18.211,11.675,5.138,-1.489,-28.007,-34.547,-41.088,-47.137,-28.173,-28.371,-34.915,-40.966,-21.912,-28.459,-28.658,-34.727,-13.992,-20.543,-20.744,-26.786,-4.767,-11.321,-17.876,-17.791,-0.564,-7.122,-13.68,-13.884,-20.444])

  ph3=np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-135.901,-91.414,0,130.5,60.378,95.843,148.729,107.46,144.297,168.156,-179.108,152.663,152.567,161.704,167.438,145.606,145.553,154.239,165.092,-168.418,-170.972,-171.029,-171.055,172.112,178.735,-175.725,-175.889,-179.217,-171.752,-166.84,-167.466,170.426,176.507,-175.792,-170.539,170.649,177.201,-176.732,-169.359,-179.166,-172.327,-165.135,-157.076,-167.157,-167.23,-160.92,-155.934,-177.822,-170.796,-170.872,-164.012,-177.097,-170.165,-170.244,-162.306,-172.141,-164.957,-157.943,-158.841,176.845,-176.363,-168.613,-169.865,168.57,175.954,-176.987,-169.937,-169.293,-162.231,-155.167,-149.032,-176.667,-169.682,-162.658,-156.315,177.194,177.1,-175.992,-169.233,-170.41,-170.508,-163.332,-156.892,-166.986,-159.977,-160.071,-153.41,-178.846,-171.918,-164.726,-165.562,173.445,-179.593,-172.637,-173.309,171.966,179.22,-173.83,-166.907,-173.729,-166.453,-159.492,-152.837,-157.887,-150.954,-143.863,-137.358,-146.102,-146.22,-139.28,-132.429,-129,-122.067,-122.189,-115.206,-167.767,-160.842,-160.966,-154.582,-170.467,-163.546,-156.627,-157.298,-179.49,-172.622,-165.757,-166.525,167.49,174.398,-178.71,-172.676,151.659,158.591,165.447,172.042,158.606,165.416,172.328,179.043,-178.869,-179.009,-172.12,-165.466,-168.628,-168.7,-161.862,-155.295,-159.522,-152.676,-152.822,-146.678,-171.206,-164.336,-157.468,-158.2,-173.744,-166.879,-160.041,-160.858,178.341,-174.801,-167.952,-161.652,176.478,-176.676,-169.827,-163.462,177.473,-175.688,-168.815,-162.408,-177.443,-177.606,-170.769,-164.315,-174.687,-167.855,-168.021,-161.724,-179.912,-173.095,-173.264,-167.045,173.248,-179.933,-173.077,-173.544,-179.116,-172.309,-165.499,-166.075,-174.782,-167.976,-161.171,-154.849,-171.762,-164.949,-158.151,-151.791,-171.927,-165.133,-158.341,-152.135,-169.354,-169.54,-162.754,-156.514,-171.037,-171.226,-164.447,-158.163,-170.03,-163.257,-163.45,-157.143,-168.666,-161.891,-155.117,-155.798,-169.806,-163.045,-156.285,-157.115,-177.411,-170.646,-163.893,-157.694,174.888,-178.363,-171.617,-165.328,169.426,176.168,-177.092,-170.704,-178.883,-179.093,-172.359,-165.789,-168.268,-161.54,-161.753,-155.265,-160.874,-154.153,-154.368,38.983,46.123,52.838,59.554,59.349,-160.332,-153.623,-146.915,142.195,138.12,144.826,151.536,158.276,126.647,133.344,140.038,146.909,52.39,59.083,65.771,72.444,47.95,47.717,54.4,61.099,174.097,173.861,-179.444,-172.737,-162.812,-156.138,-156.378,-149.863,86.823,93.604,100.267,99.963,175.257,-178.086,-171.431,-172.104,176.479,-176.857,-170.227,-164.114,-66.423,-59.776,-53.135,-46.446,-174.736,-168.098,-161.468,-155.049,-152.061,-152.317,-145.661,-140.85,-168.109,-161.458,-161.718,-155.52,-169.054,-162.437,-162.569,-156.378,-168.011,-161.4,-154.791,-155.435,-166.503,-159.898,-153.295,-153.962,-163.914,-157.316,-150.719,-144.529,-163.626,-157.034,-150.444,-144.337,-165.475,-158.89,-152.306,-146.276,-163.246,-163.526,-156.95,-150.797,-165.151,-165.435,-158.866,-152.681,-163.827,-157.262,-157.549,-151.41,-164.887,-158.329,-151.772,-152.388,-161.216,-154.664,-148.115,-148.975,-164.992,-158.447,-151.904,-146.053,-173.584,-167.045,-160.509,-154.491,-179.526,-172.995,-166.465,-160.311,-170.797,-170.95,-164.426,-158.271,-169.183,-162.664,-162.973,-156.859,-167.116,-160.604,-160.916,-154.758,28.662,35.177,41.679,41.537,-169.011,-162.513,-156.016,-156.997,15.581,22.071,28.561,35.065,-167.496,-161.011,-154.528,-148.388,-166.849,-160.37,-153.893,-147.874,-162.584,-162.913,-156.442,-151.625,-128.294,-128.626,-122.17,-115.615,-107.051,-100.594,-100.93,-94.042,-80.101,-73.65,-67.201,-67.413,-50.905,-44.461,-38.022,-38.364,-163.758,-157.314,-150.86,-144.914,1.786,8.217,14.648,21.053,-171.523,-165.097,-158.674,-152.621,-163.555,-163.908,-157.492,-151.424,-162.926,-156.515,-156.873,-150.814,-163.387,-156.983,-157.343,-151.255,-164.589,-158.192,-151.796,-152.452,-166.323,-159.932,-153.543,-153.911,-147.525])

  fitDelay(ph1)
  fitDelay(ph2)
  fitDelay(ph3)
  fitDelay(zeroBadFreqs(ph1))
  fitDelay(zeroBadFreqs(ph2))
  fitDelay(zeroBadFreqs(ph3))

