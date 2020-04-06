from __future__ import print_function
from builtins import range
import sys


# awk '{if(NF>0){print "[\"" $1 "\",\"" $2 "\"],";}}' rcv.list  > rcv.py

rcv_list= [
["rcv01","Tile011"],
["rcv01","Tile012"],
["rcv01","Tile013"],
["rcv01","Tile014"],
["rcv01","Tile015"],
["rcv01","Tile016"],
["rcv01","Tile017"],
["rcv01","Tile018"],

["rcv01","LBA1"],
["rcv01","LBA2"],
["rcv01","LBA3"],
["rcv01","LBA4"],
["rcv01","LBA5"],
["rcv01","LBA6"],
["rcv01","LBA7"],
["rcv01","LBA8"],

["rcv02","Tile131"],
["rcv02","Tile132"],
["rcv02","Tile133"],
["rcv02","Tile134"],
["rcv02","Tile135"],
["rcv02","Tile136"],
["rcv02","Tile137"],
["rcv02","Tile138"],

["rcv03","HexE17"],
["rcv03","HexE18"],
["rcv03","HexE19"],
["rcv03","HexE20"],
["rcv03","HexE21"],
["rcv03","HexE22"],
["rcv03","HexE23"],
["rcv03","HexE24"],

["rcv03","LBF1"],
["rcv03","LBF2"],
["rcv03","LBF3"],
["rcv03","LBF4"],
["rcv03","LBF5"],
["rcv03","LBF6"],
["rcv03","LBF7"],
["rcv03","LBF8"],


["rcv04","HexE25"],
["rcv04","HexE26"],
["rcv04","HexE27"],
["rcv04","HexE28"],
["rcv04","HexE29"],
["rcv04","HexE30"],
["rcv04","HexE31"],
["rcv04","HexE32"],

["rcv04","LBG1"],
["rcv04","LBG2"],
["rcv04","LBG3"],
["rcv04","LBG4"],
["rcv04","LBG5"],
["rcv04","LBG6"],
["rcv04","LBG7"],
["rcv04","LBG8"],

["rcv05","HexS21"],
["rcv05","HexS22"],
["rcv05","HexS23"],
["rcv05","HexS24"],
["rcv05","HexS25"],
["rcv05","HexS26"],
["rcv05","HexS27"],
["rcv05","HexS28"],

["rcv05","Til051"],
["rcv05","Til052"],
["rcv05","Til053"],
["rcv05","Til054"],
["rcv05","Til055"],
["rcv05","Til056"],
["rcv05","Til057"],
["rcv05","Til058"],

["rcv06","Tile141"],
["rcv06","Tile142"],
["rcv06","Tile143"],
["rcv06","Tile144"],
["rcv06","Tile145"],
["rcv06","Tile146"],
["rcv06","Tile147"],
["rcv06","Tile148"],

["rcv07","Tile071"],
["rcv07","Tile072"],
["rcv07","Tile073"],
["rcv07","Tile074"],
["rcv07","Tile075"],
["rcv07","Tile076"],
["rcv07","Tile077"],
["rcv07","Tile078"],

["rcv08","Tile081"],
["rcv08","Tile082"],
["rcv08","Tile083"],
["rcv08","Tile084"],
["rcv08","Tile085"],
["rcv08","Tile086"],
["rcv08","Tile087"],
["rcv08","Tile088"],

["rcv08","LBB1"],
["rcv08","LBB2"],
["rcv08","LBB3"],
["rcv08","LBB4"],
["rcv08","LBB5"],
["rcv08","LBB6"],
["rcv08","LBB7"],
["rcv08","LBB8"],

["rcv09","Tile091"],
["rcv09","Tile092"],
["rcv09","Tile093"],
["rcv09","Tile095"],
["rcv09","Tile096"],
["rcv09","Tile097"],
["rcv09","Tile098"],

["rcv09","LBD1"],
["rcv09","LBD2"],
["rcv09","LBD3"],
["rcv09","LBD5"],
["rcv09","LBD6"],
["rcv09","LBD7"],
["rcv09","LBD8"],

["rcv10","Tile101"],
["rcv10","Tile102"],
["rcv10","Tile103"],
["rcv10","Tile104"],
["rcv10","Tile105"],
["rcv10","Tile106"],
["rcv10","Tile107"],
["rcv10","Tile108"],

["rcv11","Tile111"],
["rcv11","Tile112"],
["rcv11","Tile113"],
["rcv11","Tile114"],
["rcv11","Tile115"],
["rcv11","Tile116"],
["rcv11","Tile117"],
["rcv11","Tile118"],

["rcv12","Tile121"],
["rcv12","Tile122"],
["rcv12","Tile123"],
["rcv12","Tile124"],
["rcv12","Tile125"],
["rcv12","Tile126"],
["rcv12","Tile127"],
["rcv12","Tile128"],

["rcv13","HexE1"],
["rcv13","HexE2"],
["rcv13","HexE3"],
["rcv13","HexE4"],
["rcv13","HexE5"],
["rcv13","HexE6"],
["rcv13","HexE7"],
["rcv13","HexE8"],

["rcv13","LBE1"],
["rcv13","LBE2"],
["rcv13","LBE3"],
["rcv13","LBE4"],
["rcv13","LBE5"],
["rcv13","LBE6"],
["rcv13","LBE7"],
["rcv13","LBE8"],

["rcv14","Tile021"],
["rcv14","Tile022"],
["rcv14","Tile023"],
["rcv14","Tile024"],
["rcv14","Tile025"],
["rcv14","Tile026"],
["rcv14","Tile047"],
["rcv14","Tile028"],

["rcv14","LBC1"],
["rcv14","LBC2"],
["rcv14","LBC3"],
["rcv14","LBC4"],
["rcv14","LBC5"],
["rcv14","LBC6"],
["rcv14","LBC8"],
["rcv14","LBC8"],

["rcv15","Tile151"],
["rcv15","Tile152"],
["rcv15","Tile153"],
["rcv15","Tile154"],
["rcv15","Tile155"],
["rcv15","Tile156"],
["rcv15","Tile157"],
["rcv15","Tile158"],

["rcv16","Tile161"],
["rcv16","Tile161"],
["rcv16","Tile163"],
["rcv16","Tile164"],
["rcv16","Tile165"],
["rcv16","Tile166"],
["rcv16","Tile167"],
["rcv16","Tile168"]
]


def find_tile_rcv(tile_name) :
   for i in range(0,len(rcv_list)):
      if rcv_list[i][1] == tile_name :
         return rcv_list[i][0]
   
   return "unknown"

   

if __name__ == "__main__":
   tile_id = "Tile011"
   if len(sys.argv) >= 2 :
      tile_id = sys.argv[1]

   rcv_id = find_tile_rcv(tile_id)
   
   print("Tile %s is connected to receiver %s" % (tile_id,rcv_id))