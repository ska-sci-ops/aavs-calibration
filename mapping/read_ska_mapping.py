# Based on westf/read_data_asd.py
# 
# Usage :
#    Save Excel Sheet (EDA2) , the google doc used is : 
#    to csv file and use "," as delimiter and nothing as string delimiter :
#    cd /home/msok/Desktop/EDA2/doc/hardware/setup
#    EDA2 with "reversed" lower inputs of TPMs      :     python ~/bighorns/software/analysis/scripts/python/read_ska_mapping.py --infile=20190621_BRIDGING_EDA2.csv
#    AAVS1.5 with non-reversed lower inputs of TPMs :     python ~/bighorns/software/analysis/scripts/python/read_ska_mapping.py --infile=20190621_BRIDGING_AAVS1d5.csv --outfile=antenna_locations_auto_AAVS1d5.txt --non_reversed
# 
# If Excel file format (columns) change just modify the mapping dictrionary : Excel_Columns_Map (set proper column numbers)

import pandas as pd
import xlrd 
import csv
# import json
import cPickle as pickle

import numpy
import sys
import matplotlib.pyplot as pyplot
import copy
import math
import os,re,errno
from lmfit import *
from lmfit.models import GaussianModel,LinearModel,PolynomialModel
from optparse import OptionParser,OptionGroup


# mapping from TPM antennas to RX (see document ~/Desktop/EDA2/logbook/eda2_pointing.odt where I have details of mapping explanations ) 
# also ...

# RX -> DATA_INDEX 
preadu_tpm_input_mapping = { 1: 0, 
                             2: 1, 
                             3: 2, 
                             4: 3, 
                             5: 8, 
                             6: 9, 
                             7: 10,
                             8: 11, 
                             9: 15, 
                             10: 14, 
                             11: 13, 
                             12: 12, 
                             13: 7, 
                             14: 6, 
                             15: 5, 
                             16: 4
                           }

# DATA_INDEX -> RX 
antenna_rx_mapping       = {
                              0: 1, 
                              1: 2, 
                              2: 3, 
                              3: 4, 
                              8: 5, 
                              9: 6, 
                              10: 7,
                              11: 8, 
                              15: 9, 
                              14: 10,
                              13: 11, 
                              12: 12, 
                              7: 13, 
                              6: 14, 
                              5: 15, 
                              4: 16
                            }


# when instead of antennas being connect in opposite order ( down -> top) at the lower half of TPM inputs, they are connect top -> down 
reversed_tpm_input_mapping = {
                                1: 1,
                                2: 2,
                                3: 3,
                                4: 4,
                                5: 5,
                                6: 6,
                                7: 7,
                                8: 8,
                                9: 16,
                                10: 15,
                                11: 14,
                                12: 13,
                                13: 12,
                                14: 11,
                                15: 10,
                                16: 9
                             }

g_ribbon_column_name = "Ribbon"

Excel_Columns_Map = {
                       "antenna"     : 0,
                       "north_south" : 1,
                       "east_west"   : 2,
                       "z"           : 3,
                       "tile_id"     : 4,
                       "smart_box"   : 7,
                       "fem"         : 8,
                       "fibre"       : 9,
                       "colour"      : 10,
                       "fobot"      : 11,       
                       "ribbon"      : 12,
                       "tpm"         : 13,
                       "rx"          : 14                                              
                    }

g_verb=0

class Antenna :
   antenna_base  = "unknown"
   north_south    = 0.00
   east_west      = 0.00
   z              = 0.00
   tile_id        = 0
   smart_box      = 0
   fem            = 0 
   fibre          = 0 
   colour         = "unknown"
   fobot          = 'U' 
   ribbon         = "unknown"
   tpm            = 0
   rx             = 0
   
   tpm_input      = -1
   data_index     = -1
   
      
   
   def __init__( self , antenna_base="unknown" ):
      self.antenna_base  = antenna_base
      self.north_south    = 0.00
      self.east_west      = 0.00
      self.z              = 0.00
      self.tile_id        = 0
      self.smart_box      = 0
      self.fem            = 0 
      self.fibre          = 0 
      self.colour         = "unknown"
      self.fobot          = 'U' 
      self.ribbon         = "unknown"
      self.tpm            = 0
      self.rx             = 0
      
      self.tpm_input      = -1
      self.data_index     = -1

   def __repr__(self) :
       out_str =  "Antenna%s , (%.4f,%.4f,%.4f) tile_id=%d, tpm=%s, rx=%d, tpm_input=%d, data_index=%d" % (self.antenna_base,self.east_west,self.north_south,self.z,self.tile_id,self.tpm,self.rx,self.tpm_input,self.data_index)
       
       return out_str

   def __str__(self) :
       return "member of Antenna"


def parse_options():
   usage="Usage: %prog [options]\n"
   usage+='\tRead and plot WestFarmers data\n'
   parser = OptionParser(usage=usage,version=1.00)
   parser.add_option('--infile',dest="infile",default="20190621_BRIDGING.csv", help="Input file can either be csv or xlsx (Excel) [default %default]") # 20190621_BRIDGING.xlsx
   parser.add_option('--outfile','--out_file','--out',dest="outfile",default="antenna_locations_auto.txt", help="Output file [default %default]") # antenna_locations_auto.txt
   parser.add_option('--decimal',dest="decimal",default=".", help="Decimal point floating numbers [default %default]")
   parser.add_option('--non_reversed','--top_down_order',dest="tpm_input_reversed",default=False,action="store_false",help="Reversed order on TPM input lower half of inputs other way around [default %default]")
   parser.add_option('--reversed','--down_top_order',dest="tpm_input_reversed",default=False,action="store_true",help="Reversed order on TPM input lower half of inputs other way around [default %default]")
   parser.add_option('--tpm_list','--tpms',dest="tpm_list",default=None, help="TPM list - to only include these TPMs [default %default - empty means use all]") 
   parser.add_option('--print_tpm','--add_tpm',dest="print_tpm",default=False,action="store_true",help="Add TPM to output [default %default]")
   parser.add_option('--use_all_ants','--use_all',dest='use_all_ants',default=False,action="store_true",help="Use all antennas (ignore Ribbon column as indicator if antenna is connected) [default %default]")
#   parser.add_option('-d','--device_id','--device',dest="device_id",default=None, help="Device ID [default %default]")
#   parser.add_option('-t','-c','--crop_type',dest="crop_type",default="Wheat", help="Plant type [default %default]")
#   parser.add_option('-o','--outfile','--outf',dest="output_file",default="results.txt", help="Results outputfile [default %default]")
#   parser.add_option('--filecolumn',dest="filecolumn",default=" ", help="Column with file name in csv file [default %default]")
   (options, args) = parser.parse_args()
   return (options, args)   

def print_options(options,args,tpm_list) :

   print "####################################################"
   print "PARAMTERS :"
   print "####################################################"
   print "Input file  = %s" % (options.infile)
   print "Output file = %s" % (options.outfile)
   print "TPM list    = %s (%s)" % (options.tpm_list,tpm_list)
   print "print_tpm   = %s" % (options.print_tpm)
   print "Reversed    = %s" % (options.tpm_input_reversed)
   print "Decimal     = %s" % (options.decimal)
   print "Use all ANTs = %s" % (options.use_all_ants)
   print "####################################################"

   
   return (options, args)



def mkdir_p(path):
   try:
      os.makedirs(path)
   except OSError as exc: # Python >2.5
      if exc.errno == errno.EEXIST:
         pass
      else: raise
       
       
def is_float(input):
  try:
    num = float(input)
  except ValueError:
    return False
  return True

def is_number(s):
    """ Returns True is string is a number. """
    try:
        int(s)
        return True
    except ValueError:
        return False



def read_spectrum( file_name ) :

   data_x=[]
   data_y=[]
   file=open( file_name,'r')
   
   # reads the entire file into a list of strings variable data :
   data=file.readlines()
   for line in data : 
       words = line.split(' ')

       if line[0] == '#' :
           continue

       if line[0] != "#" :
           x=float(words[0+0])
           y=float(words[1+0])
      
       data_x.append(x)
       data_y.append(y)

       file.close()
   
   print "Read %d points from file %s" % (len(data_x),file_name)
   return (data_x,data_y)    


def excel2csv( xls_file = "20190621_BRIDGING.xlsx" , csv_file="20190621_BRIDGING.csv", sheet_name="EDA-2") :
#    file="140818_Combined_Data_for_Curtin_2018.csv"
    wb = xlrd.open_workbook( xls_file )
    sheet = wb.sheet_by_name( sheet_name )

    csv_f = open(csv_file,"wb")
    wr = csv.writer( csv_f, quoting=csv.QUOTE_ALL)
    for rownum in xrange(sheet.nrows) :
        wr.writerow(sheet.row_values(rownum))
    csv_f.close()


def read_mapping( file="20190621_BRIDGING.csv",
                  tpm_input_reversed = True,
                  tpm_list           = None,
                  decimal            = ".",
                  use_all_ants       = False
                ) : 
    global g_ribbon_column_name 
                     
    print "Reading file %s" % (file)
   
    mapping_data = pd.read_csv(file,low_memory=False,decimal=decimal) # or ","

    connected_antennas = None
    if use_all_ants :
       connected_antennas = mapping_data.copy()
    else :
       connected_antennas = mapping_data[(mapping_data[ g_ribbon_column_name ] != "-")]
    connected_count = connected_antennas.shape[0]
    
    print "connected_antennas count = %d" % (len(connected_antennas))

#    for idx in range(0,n_ant) : 
#       ribbon = mapping_data['Ribbon'][idx]
#       print "%d ribbon = %s" % (idx,ribbon)
#       if mapping_data['Ribbon']

    antenna_list=[]
    tpms_unique=[]
    data_index=[]
    
    for i, r in enumerate(connected_antennas.values):
       tpm = r[Excel_Columns_Map['tpm']] 
       
       if tpm_list is not None :
          if tpm not in tpm_list :
             print "WARNING : tpm = %s not in list %s -> skipped" % (tpm,tpm_list)
             continue
    
       if tpm not in tpms_unique :
          print "Adding unique TPM = %s" % (tpm)
          tpms_unique.append( tpm )
          
       # using mapping Excel_Columns_Map[''] but original "easy" version commented on the right           
       antenna             = Antenna( r[ Excel_Columns_Map['antenna'] ] ) # r[0]
       antenna.north_south = float( r[ Excel_Columns_Map['north_south'] ] ) # r[1]
       antenna.east_west   = float( r[ Excel_Columns_Map['east_west'] ] ) # r[2]
       antenna.z           = float( r[ Excel_Columns_Map['z'] ] ) # r[2]
       antenna.tile_id     = int( r[ Excel_Columns_Map['tile_id'] ] ) # r[3] 
       antenna.smart_box   = int( r[ Excel_Columns_Map['smart_box'] ] ) # r[6] 
       antenna.fem         = r[ Excel_Columns_Map['fem'] ]        # r[7]
       antenna.fibre       = int( r[ Excel_Columns_Map['fibre'] ] ) # r[8]
       antenna.colour      = r[ Excel_Columns_Map['colour'] ]        # r[9]
       antenna.fobot       = r[ Excel_Columns_Map['fobot'] ]       # r[10] 
       antenna.ribbon      = r[ Excel_Columns_Map['ribbon'] ]       # r[11]
       antenna.tpm         = tpm                                 # r[12]
       antenna.rx          = int( r[ Excel_Columns_Map['rx'] ] ) # r[13]
       
       # apply mappings :
       antenna.tpm_input = antenna.rx       
       if tpm_input_reversed :
          if antenna.rx >= 9 :
             antenna.tpm_input = reversed_tpm_input_mapping[ antenna.rx ]
       
       tpm_offset = 16*( len(tpms_unique)-1 )
       antenna.data_index = preadu_tpm_input_mapping[antenna.tpm_input] + tpm_offset
       
       antenna_list.append( copy.deepcopy(antenna) )
       

    for dataidx in range(0,connected_count) :
       for antenna in antenna_list :
          if antenna.data_index == dataidx :
              data_index.append( antenna )
              break
        

    print "TPMs = %s" % (tpms_unique)
    


    return (connected_antennas,tpms_unique,antenna_list,data_index)


def antenna2dataindex( csv_file="20190621_BRIDGING.csv",
                       tpm_input_reversed = True,
                       outfile           = "antenna_locations_auto.txt",
                       tpm_list          = None,
                       options           = None
                     ) : 
                         
    (connected_antennas,tpms_unique,antenna_list,data_index) = read_mapping( file=csv_file, tpm_input_reversed=tpm_input_reversed, tpm_list=tpm_list, decimal=options.decimal, use_all_ants=options.use_all_ants )
    n_ant_connected = connected_antennas.shape[0]

    out_f = open( outfile, "w" )    
    for ant in data_index:
       line = "Ant%03d %.4f %.4f %.4f" % (int(ant.antenna_base),ant.east_west,ant.north_south,ant.z)
       if options.print_tpm :
          line += (" %d" % ant.tpm)
       print line
       
       out_f.write(line + "\n")
       
    out_f.close()   
    
    return (connected_antennas,tpms_unique,antenna_list,data_index)
    
if __name__ == '__main__':
   (options, args) = parse_options()
   
   tpm_list = None 
   if options.tpm_list is not None :
       tpm_list=options.tpm_list.split(",")
       tpm_list=map(int,tpm_list)
   
   print_options( options, args, tpm_list) 
   
  
   csv_file=options.infile
   if options.infile.find(".xlsx") >= 0 :
      print "Converting Excel -> csv file ..."
      csv_file = options.infile.replace('.xlsx', '.csv' )
      excel2csv( xls_file=options.infile, csv_file=csv_file )      
   else :
      print "CSV file provided -> no converting required"

   (connected_antennas,tpms_unique,antenna_list,data_index) = antenna2dataindex( csv_file=csv_file, tpm_input_reversed=options.tpm_input_reversed, outfile=options.outfile, tpm_list=tpm_list, options=options )
   

