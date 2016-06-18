import os
from datetime import datetime, timedelta, tzinfo
from time import mktime
import tzlocal
from array import array
from appd.request import AppDynamicsClient
import sys, getopt

def changedate(datestr):
    date_obj = datetime.strptime(datestr, "%Y%m%d%H%M")
    return date_obj

def freq_to_mins(md):
    FREQ_MAP = {'ONE_MIN': 1, 'TEN_MIN': 10, 'SIXTY_MIN': 60}
    return FREQ_MAP[md.frequency]

def duration_length(start,end,freq):
    length = int((end - start).seconds / 60 / freq) + int((end-start).days * 24 * 60 / freq)
    return length

start_time = end_time = ''

try:
  opts, args = getopt.getopt(sys.argv[1:],"s:e:o:",["starttime=","endtime=","outputfile="])
except getopt.GetoptError:
  print('Format: MetricExport_OverallAppPerformance.py -s YYYYmmddHH24MM -e YYYYmmddHH24MM [-o "output directory path"] ')
  print ('Eg: MetricExport_OverallAppPerformance.py -s 201605120100 -e 201605130100 [-o "/home/root/"] ')
  sys.exit(2)
for opt, arg in opts:
  if opt in ("-s", "--starttime"):
     start_time = changedate(arg.strip())
  elif opt in ("-e", "--endtime"):
     end_time = changedate(arg.strip())
  elif opt in ("-o", "--outputpath"):
      output = arg.strip()


if (start_time==''):
    print('Start time is a mandatory value')
    print('Format: MetricExport_OverallAppPerformance.py   -s YYYYmmddHH24MM -e YYYYmmddHH24MM [-o "output directory path"] ')
    print('Eg: MetricExport_OverallAppPerformance.py  -s 201605120100 -e 201605130100 [-o "/home/root/"] ')
    sys.exit(2)
elif (end_time==''):
    print('End time is a mandatory value')
    print('Format: MetricExport_OverallAppPerformance.py   -s YYYYmmddHH24MM -e YYYYmmddHH24MM [-o "output directory path"] ')
    print('Eg: MetricExport_OverallAppPerformance.py  -s 201605120100 -e 201605130100 [-o "/home/root/"] ')
    sys.exit(2)
    

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
account = "test"

c = AppDynamicsClient(account=account, base_url=baseurl, username=username, password=password)


#Adding it hard coded for backends to be pulled from this tier
apps = ['BRE-DES']
metrics=['Calls per Minute', 'Number of Slow Calls', 'Number of Very Slow Calls', 'Stall Count', 'Average Response Time (ms)']
metric_path =  'Overall Application Performance|*'
for app in apps:
    export_header = 'datetime'
    md_list = c.get_metrics(metric_path, app , time_range_type='BETWEEN_TIMES', end_time=end_epoch,
                            start_time=start_epoch, rollup=False)
    freq = freq_to_mins(md_list[0])
    mv = [''] * duration_length(start_time,end_time,freq)
    for md in md_list:
        if len(md.values) > 0:
            # Get the last two components of the metric path. This should be 'backend_name|metric_name'.
            backend_name, metric_name = md.path.split('|')[-2:]
            if metric_name in metrics:
                export_header = export_header + ',' + metric_name
                if mv[0] != '' :
                    mv = [s + '-' if s.endswith(',') else s for s in mv ]
                    mv = [s + ',' if s.__ne__('') else s for s in mv]
                for i in range(0, len(md.values)):
                    minute_index = int((md.values[i].start_time_ms - start_epoch) / 1000 / 60/ freq)
                    if '' == mv[minute_index]:
                        mv[minute_index] = str(md.values[i].start_time) + ','
                    mv[minute_index] = mv[minute_index] + str(md.values[i].value)
    mv = [s + '-' if s.endswith(',') else s for s in mv]

    if export_header!='datetime':
        filename = app.replace('/', '') + '_' + start_time.strftime('%Y%m%d%H%M') + '_' + end_time.strftime('%Y%m%d%H%M') + '.csv'
        fullfilepath=''
        # complete directory path where we need to store the data files
        if output == '':
            fullfilepath = './' + app.replace('/', '') + '_' + start_time.strftime('%Y%m%d%H%M') + '_' + end_time.strftime('%Y%m%d%H%M') + '.csv'
        else :
            if not os.path.exists(output):
                os.makedirs(output)
                fullfilepath = output + '/' +  filename
            else:
                fullfilepath = output + '/' + filename


        # file for each backend is a combination of the backend name & week's Monday date
        #filename = dir + '/' + appname.replace('/', '') + '_' + start_time.strftime('%Y%m%d%H%M') + '_' + end_time.strftime('%Y%m%d%H%M') + '.csv'
        if not os.path.exists(fullfilepath):
            f = open(fullfilepath, 'a')
            f.write(export_header)
        else:
            f = open(fullfilepath, 'a')
        for i in range(0, len(mv)):
            if '' != mv[i]:
               f.write('\n')
               f.write(mv[i])
        f.close()