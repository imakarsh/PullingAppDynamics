from requests.auth import HTTPBasicAuth
import requests, sys
import json,csv
import sys, getopt
from datetime import datetime, timedelta, tzinfo
from time import mktime
import os
from collections import Counter

def changedate(datestr):
    date_obj = datetime.strptime(datestr, "%Y%m%d%H%M")
    return date_obj

start_time = end_time = appname = ''

try:
  opts, args = getopt.getopt(sys.argv[1:],"s:e:a:",["starttime=","endtime=","appname="])
except getopt.GetoptError:
  print('Format: MetricExport_OverallAppPerformance.py -s YYYYmmddHH24MM -e YYYYmmddHH24MM -a "Appname" ')
  print('Eg: MetricExport_OverallAppPerformance.py -s 201605120100 -e 201605130100 -a "eStore-prod" ')
  sys.exit(2)
for opt, arg in opts:
  if opt in ("-s", "--starttime"):
     start_time = changedate(arg.strip())
  elif opt in ("-e", "--endtime"):
     end_time = changedate(arg.strip())
  elif opt in ("-a", "--appname"):
     appname = arg.strip()


if (start_time==''):
    print('Start time is a mandatory value')
    print('Format: MetricExport_OverallAppPerformance.py -s YYYYmmddHH24MM -e YYYYmmddHH24MM -a "Appname" ')
    print('Eg: MetricExport_OverallAppPerformance.py -s 201605120100 -e 201605130100 -a "eStore-prod" ')
    sys.exit(2)
elif (end_time==''):
    print('End time is a mandatory value')
    print('Format: MetricExport_OverallAppPerformance.py -s YYYYmmddHH24MM -e YYYYmmddHH24MM -a "Appname" ')
    print('Eg: MetricExport_OverallAppPerformance.py -s 201605120100 -e 201605130100 -a "eStore-prod" ')
    sys.exit(2)
elif (appname==''):
    print('App name is a mandatory value')
    print('Format: MetricExport_OverallAppPerformance.py -s YYYYmmddHH24MM -e YYYYmmddHH24MM -a "Appname" ')
    print('Eg: MetricExport_OverallAppPerformance.py -s 201605120100 -e 201605130100 -a "eStore-prod" ')
    sys.exit(2)

end_epoch = int(mktime(end_time.timetuple())) * 1000
start_epoch = int(mktime(start_time.timetuple())) * 1000


url = 'https://test.saas.appdynamics.com/controller/rest/applications/' + appname + '/events?time-range-type=BETWEEN_TIMES&start-time=' + str(start_epoch) + '&end-time=' + str(end_epoch) + '&event-types=%20APPLICATION_ERROR,DIAGNOSTIC_SESSION&severities=ERROR&output=JSON'
resp = requests.get(url, auth=HTTPBasicAuth('user', 'pass'))
jresp = json.loads(resp._content)
export_header = "URL\tErrorMessage"
# complete directory path where we need to store the data files
dir='.'
# file for each backend is a combination of the backend name & week's Monday date
filename = dir + '/' + appname.replace('/', '') + '_Errors_' + start_time.strftime('%Y%m%d%H%M') + '_' + end_time.strftime('%Y%m%d%H%M') + '.tsv'
if not os.path.exists(filename):
    f = open(filename, 'a')
    f.write(export_header)
else:
    f = open(filename, 'a')

for k in range(len(jresp)):
    f.write('\n')
    f.write(jresp[k]["deepLinkUrl"].encode("utf-8") + '\t' + jresp[k]["summary"].encode("utf-8").replace('\n', ' ').replace('\r', ' '))
f.close()

errorlist = []
header=False
with open(filename) as tsv:
    for  line in csv.reader(tsv, dialect="excel-tab"):
         if header :
             errorlist.append(line[1])
         else :
             header = True

c = Counter(errorlist)
errorgroupfile = dir + '/' + appname.replace('/', '') + '_ErrorsGrouped_' + start_time.strftime('%Y%m%d%H%M') + '_' + end_time.strftime('%Y%m%d%H%M') + '.csv'
with open(errorgroupfile,'w') as f:
    for k,v in  c.most_common():
        f.write( "{} {}\n".format(k,v) )