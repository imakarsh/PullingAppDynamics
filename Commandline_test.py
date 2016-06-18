#!/usr/bin/python

import sys, getopt
import tzlocal
from datetime import datetime, timedelta
from dateutil import tz


def changedate(datestr):
    date_obj = datetime.strptime(datestr, "%Y%m%d%H%M")
    return date_obj

def main(argv):
   try:
      opts, args = getopt.getopt(argv,"t:n:s:e:d:z:",["tier=","appname=","starttime=","endtime=","duration=","timezone="])
   except getopt.GetoptError:
      print('ApdDlMetri.py -t {app|tier|bt}  -n "name of app, tier or bt" -s YYYYddmmHH24MM {-e YYYYddmmHH24MM | -d d5h4m10  } [-z GMT] ')
      sys.exit(2)
   for opt, arg in opts:
      if opt in ("-t", "--tier"):
         tier = arg.strip()
      elif opt in ("-n", "--appname"):
         appname = arg.strip()
      elif opt in ("-s", "--starttime"):
         starttime = arg.strip()
      elif opt in ("-e", "--endtime"):
         endtime = arg.strip()
      elif opt in ("-d", "--duration"):
         duration = arg.strip()
      elif opt in ("-z", "--timezone"):
         timezone = arg.strip()
         
   if(timezone!=''):
        zone=tz.gettz(timezone)
        print(zone)
     #   print(starttime.replace(tzinfo=zone))

   print(tzlocal.get_localzone())

   print ('tier file is', tier)
   print ('appname file is', appname)
   print ('starttime file is', changedate(starttime)._tzinfo)
   print ('endtime file is', changedate(endtime)._day)
   print ('timezone file is', timezone)
   
   

if __name__ == "__main__":
   main(sys.argv[1:])