import os
from datetime import datetime, timedelta
from time import mktime
import time
import sys, getopt
import requests, json
from requests.auth import HTTPBasicAuth


def changedate(datestr):
    date_obj = datetime.strptime(datestr, "%Y%m%d%H%M")
    return date_obj


def freq_to_mins(md):
    FREQ_MAP = {'ONE_MIN': 1, 'TEN_MIN': 10, 'SIXTY_MIN': 60}
    return FREQ_MAP[md['frequency']]


def duration_length(start, end, freq):
    length = int((end - start).seconds / 60 / freq) + int((end - start).days * 24 * 60 / freq)
    return length


start_time = end_time = ''

try:
    opts, args = getopt.getopt(sys.argv[1:], "s:e:o:", ["starttime=", "endtime=", "outputfile=" ])
except getopt.GetoptError:
    print(
    'Format: MetricExport_OverallAppPerformance.py -s YYYYmmddHH24MM [-o "output directory path"] ')
    print ('Eg: MetricExport_OverallAppPerformance.py -s 201605120100 [-o "/home/root/"] ')
    sys.exit(2)
for opt, arg in opts:
    if opt in ("-s", "--starttime"):
        start_time = changedate(arg.strip())
        end_time = changedate(datetime.strftime(datetime.now(), '%Y%m%d%H%M'))
    elif opt in ("-e", "--endtime"):
        end_time = arg.strip()
        end_time = changedate(datetime.strftime(datetime.now(), '%Y%m%d%H%M'))
    elif opt in ("-o", "--outputpath"):
        output = arg.strip()

if (start_time == ''):
    print('Start time is a mandatory value')
    print(
    'Format: MetricExport_OverallAppPerformance.py   -s YYYYmmddHH24MM [-o "output directory path"] ')
    print('Eg: MetricExport_OverallAppPerformance.py  -s 201605120100 [-o "/home/root/"] ')
    sys.exit(2)

end_epoch = int(mktime(end_time.timetuple()))
start_epoch = int(mktime(start_time.timetuple()))


# Adding it hard coded for backends to be pulled from this tier
apps = ['MBR']

metrics = ['Calls per Minute', 'Number of Slow Calls', 'Number of Very Slow Calls', 'Stall Count',
           'Average Response Time (ms)','Errors per Minute']
summetrics = ['Calls per Minute','Average Response Time (ms)','Errors per Minute']
metric_path = 'Overall Application Performance|*'
metric_name=''
prevmetric_name=''
for app in apps:
    export_header = 'datetime'
    url = 'https://test.saas.appdynamics.com/controller/rest/applications/' + app + '/metric-data?time-range-type=BEFORE_NOW&duration-in-mins='+ str(int((end_epoch-start_epoch)/60)) +'&metric-path=' + metric_path + '&rollup=false&output=JSON'
    resp = requests.get(url, auth=HTTPBasicAuth('user@account', 'pass'))
   # reader = codecs.getreader("utf-8")
    md_list = json.loads(resp._content.decode('utf-8'))

    freq = freq_to_mins(md_list[0])
    mv = ['--'] * duration_length(start_time, end_time, freq)
    columnindex=0
    for md in md_list:
        if len(md['metricValues']) > 0:
            # Get the last two components of the metric path. This should be 'backend_name|metric_name'.
            backend_name, metric_name = md['metricPath'].split('|')[-2:]
            if metric_name in metrics:
                export_header = export_header + ',' + metric_name
                if metric_name in summetrics:
                    export_header = export_header + ',' + 'Sum of ' + metric_name
                if columnindex != 0:
                    if prevmetric_name in summetrics:
                        mv = [s + '--,--' if s.endswith(',') else s for s in mv]
                        mv = [s + ',' for s in mv]
                    else :
                        mv = [s + '--' if s.endswith(',') else s for s in mv]
                        mv = [s + ',' for s in mv]
                prevmetric_name = metric_name
                for i in range(0, len(md['metricValues'])):
                    minute_index = int((md['metricValues'][i]['startTimeInMillis']/1000 - start_epoch) / 60 / freq)
                    if minute_index >= 0:
                        if mv[minute_index].startswith('--'):
                            mv[minute_index] = str(time.strftime('%m/%d/%y %I:%M:%S %p', time.localtime(md['metricValues'][i]['startTimeInMillis']/1000))).replace(' 0',' ') + ','
                            for j in range(0,columnindex):
                                mv[minute_index] = mv[minute_index] + '--,'
                        mv[minute_index] = mv[minute_index] + str(md['metricValues'][i]['value'])
                        if metric_name in summetrics:
                            mv[minute_index] = mv[minute_index] + ',' + str(md['metricValues'][i]['sum'])
                if metric_name in summetrics:
                    columnindex = columnindex + 2
                else :
                    columnindex = columnindex + 1
    if metric_name in summetrics:
        mv = [s + '--,--' if s.endswith(',') else s for s in mv]
    else :
        mv = [s + '--' if s.endswith(',') else s for s in mv]

    if export_header != 'datetime':
        filename = app.replace('/', '') + '_' + start_time.strftime('%Y%m%d%H%M') + '_' + end_time.strftime(
            '%Y%m%d%H%M') + '.csv'
        fullfilepath = ''
        # complete directory path where we need to store the data files
        if output == '':
            fullfilepath = './' + app.replace('/', '') + '_' + start_time.strftime(
                '%Y%m%d%H%M') + '_' + end_time.strftime('%Y%m%d%H%M') + '.csv'
        else:
            if not os.path.exists(output):
                os.makedirs(output)
                fullfilepath = output + '/' + filename
            else:
                fullfilepath = output + '/' + filename

        if not os.path.exists(fullfilepath):
            f = open(fullfilepath, 'a')
            f.write(export_header)
        else:
            f = open(fullfilepath, 'a')
        for i in range(0, len(mv)):
            if '--,--,--,--,--,--,--,--,--' != mv[i] and '--,--,--,--,--,--,--,--' != mv[i]:
                f.write('\n')
                f.write(mv[i])
            else :
                if i==0:
                    datetime_prev=(start_time.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)).strftime("%m/%d/%y %I:%M:%S %p")
                else:
                    datetime_prev = mv[i-1].split(",")[0]
                datetime_prev = datetime.strptime(datetime_prev, "%m/%d/%y %I:%M:%S %p") + timedelta(hours=1)
                mv[i]=datetime.strftime(datetime_prev, '%m/%d/%y %I:%M:%S %p').replace(' 0',' ') + ',--,--,--,--,--,--,--,--'
                f.write('\n')
                f.write(mv[i])
        f.close()