import os
from datetime import datetime, timedelta, tzinfo
from time import mktime
import tzlocal
from array import array
from appd.request import AppDynamicsClient
import sys, getopt
from dateutil import tz

def changedate(datestr):
    date_obj = datetime.strptime(datestr, "%Y%m%d%H%M")
    return date_obj

def freq_to_mins(md):
    FREQ_MAP = {'ONE_MIN': 1, 'TEN_MIN': 10, 'SIXTY_MIN': 60}
    return FREQ_MAP[md.frequency]

#TODO modify to extract length between time intervals
def duration_length(start,end,freq):
    length = int((end - start).seconds / 60 / freq) + int((end-start).days * 24 * 60 / freq)
    return length

tier = appname = start_time = end_time = timezone = ''

# try:
#   opts, args = getopt.getopt(sys.argv[1:],"t:n:s:e:",["tier=","appname=","starttime=","endtime="])
# except getopt.GetoptError:
#   print('Format: MetricExport_onDemand.py -t {app|tier|bt}  -n "name of app, tier or bt" -s YYYYddmmHH24MM -e YYYYddmmHH24MM ')
#   print ('Eg: MetricExport_onDemand.py -t "Business Transaction Performance|Business Transactions|RequestCenter" -n "/RequestCenter/nsapi" -s 201605120100 -e 201605130100 ')
#   sys.exit(2)
# for opt, arg in opts:
#   if opt in ("-t", "--tier"):
#      tier = arg.strip()
#   elif opt in ("-n", "--appname"):
#      appname = arg.strip()
#   elif opt in ("-s", "--starttime"):
#      start_time = changedate(arg.strip())
#   elif opt in ("-e", "--endtime"):
#      end_time = changedate(arg.strip())
#
# if(tier==''):
#     print('Tier is a mandatory value')
#     print('Format: MetricExport_onDemand.py -t {app|tier|bt}  -n "name of app, tier or bt" -s YYYYddmmHH24MM -e YYYYddmmHH24MM  [-z GMT] ')
#     print ('Eg: MetricExport_onDemand.py -t "Business Transaction Performance|Business Transactions|RequestCenter" -n "/RequestCenter/nsapi" -s 201605120100 -e 201605130100  -z IST')
# elif (appname==''):
#     print('Tier is a mandatory value')
#     print('Format: MetricExport_onDemand.py -t {app|tier|bt}  -n "name of app, tier or bt" -s YYYYddmmHH24MM -e YYYYddmmHH24MM  [-z GMT] ')
#     print ('Eg: MetricExport_onDemand.py -t "Business Transaction Performance|Business Transactions|RequestCenter" -n "/RequestCenter/nsapi" -s 201605120100 -e 201605130100  -z IST')
# elif (start_time==''):
#     print('Tier is a mandatory value')
#     print('Format: MetricExport_onDemand.py -t {app|tier|bt}  -n "name of app, tier or bt" -s YYYYddmmHH24MM -e YYYYddmmHH24MM  [-z GMT] ')
#     print ('Eg: MetricExport_onDemand.py -t "Business Transaction Performance|Business Transactions|RequestCenter" -n "/RequestCenter/nsapi" -s 201605120100 -e 201605130100  -z IST')
# elif (end_time==''):
#     print('Tier is a mandatory value')
#     print('Format: MetricExport_onDemand.py -t {app|tier|bt}  -n "name of app, tier or bt" -s YYYYddmmHH24MM -e YYYYddmmHH24MM  [-z GMT] ')
#     print ('Eg: MetricExport_onDemand.py -t "Business Transaction Performance|Business Transactions|RequestCenter" -n "/RequestCenter/nsapi" -s 201605120100 -e 201605130100  -z IST')
#

start_time = changedate("201601010000")
end_time = changedate("201601110000")

# The report will generate data for the last 2-hour period before the current hour of the current day.
# It needs to be run for every 2 hours using cron. Prefer to run it at even hours so that it runs 0,2,4,..,22 hours
#end_time = datetime.now().replace(minute=0, second=0, microsecond=0)
end_epoch = int(mktime(end_time.timetuple())) * 1000
#start_time = end_time - timedelta(hours=2)
start_epoch = int(mktime(start_time.timetuple())) * 1000
# Pulls data from Monday to Sunday into a single file for each backend.
#week_monday = start_time - timedelta(days=start_time.weekday())

# Credentials for the Client connection
username = "user"
password = "pass"
baseurl = "https://test.saas.appdynamics.com"
account = "account"

c = AppDynamicsClient(account=account, base_url=baseurl, username=username, password=password)

# Add more backend values to create additional backend extracts
#backends = ['/RequestCenter/nsapi', 'myservices/executeFormRules.execute']

#for backend_value in backends :
metric_path =  tier + '|' + appname + '|*'
metric_path = "/controller/rest/applications/eStore-prod/events"
export_header = 'datetime'
md_list = c.get_metrics('eStore-prod', time_range_type='BETWEEN_TIMES', end_time=end_epoch,
                        start_time=start_epoch, severities='APPLICATION_ERROR', eventtypes="ERROR",rollup=False)
freq = freq_to_mins(md_list[0])
mv = [''] * duration_length(start_time,end_time,freq)
for md in md_list:
    if len(md.values) > 0:
        # Get the last two components of the metric path. This should be 'backend_name|metric_name'.
        backend_name, metric_name = md.path.split('|')[-2:]
        export_header = export_header + ',' + metric_name
        if mv[0] != '' :
            mv = [s + ',' for s in mv]
        for i in range(0, len(md.values)):
            minute_index = int((md.values[i].start_time_ms - start_epoch) / 1000 / 60/ freq)
            if '' == mv[minute_index]:
                mv[minute_index] = str(md.values[i].start_time) + ','
            mv[minute_index] = mv[minute_index] + str(md.values[i].value)

# complete directory path where we need to store the data files
dir='.'
# file for each backend is a combination of the backend name & week's Monday date
filename = dir + '/' + appname.replace('/', '') + '_' + start_time.strftime('%Y%m%d%H%M') + '_' + end_time.strftime('%Y%m%d%H%M') + '.csv'
if not os.path.exists(filename):
    f = open(filename, 'a')
    f.write(export_header)
else:
    f = open(filename, 'a')
for i in range(0, len(mv)):
    if '' != mv[i]:
       f.write('\n')
       f.write(mv[i])
f.close()