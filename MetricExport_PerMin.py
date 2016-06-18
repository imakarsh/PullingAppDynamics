import os
from datetime import datetime, timedelta
from time import mktime
import time
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


# The report will generate data for the last 1-hour period before the current hour of the current day.
# It needs to be run for every 1 hours using cron. Prefer to run it at 10 minutes after every hour so that it can pull previous hour data
end_time = datetime.now()
end_epoch = int(mktime(end_time.timetuple())) * 1000
#end_time = end_time + timedelta(hours=1)
start_time = (end_time - timedelta(hours=1)).replace(minute=1, second=0, microsecond=0)
start_epoch = int(mktime(start_time.timetuple())) * 1000
durationinmins = int((end_time - start_time).total_seconds()/60)
# Pulls data from Monday to Sunday into a single file for each backend.
week_monday = start_time - timedelta(days=start_time.weekday())

# # Credentials for the Client connection
# username = myconfig.username
# password = myconfig.password
# baseurl = myconfig.baseurl
# account = myconfig.account
#
# c = AppDynamicsClient(account=account, base_url=baseurl, username=username, password=password)
#
# # Add more backend values to create additional backend extracts
# backends = myconfig.backends
# tier = myconfig.tier
#
# for backend_value in backends :
#     metric_path = tier + '|' + backend_value + '|*'
#     export_header = 'datetime'
#     md_list = c.get_metrics(metric_path, 'eStore-prod', time_range_type='BETWEEN_TIMES', end_time=end_epoch,
#                             start_time=start_epoch, rollup=False)
#     mv = [''] * 120
#     for md in md_list:
#         if len(md.values) > 0:
#             # Get the last two components of the metric path. This should be 'backend_name|metric_name'.
#             backend_name, metric_name = md.path.split('|')[-2:]
#             export_header = export_header + ',' + metric_name
#             if mv[0] != '' :
#                 mv = [s + '-' if s.endswith(',') else s for s in mv]
#                 mv = [s + ',' if s.__ne__('') else s for s in mv]
#             for i in range(0, len(md.values)):
#                 minute_index = int((md.values[i].start_time_ms - start_epoch) / 1000 / 60)
#                 if '' == mv[minute_index]:
#                     mv[minute_index] = str(md.values[i].start_time) + ','
#                 mv[minute_index] = mv[minute_index] + str(md.values[i].value)
#     mv = [s + '-' if s.endswith(',') else s for s in mv]
#

http_proxy  = "http://proxy.url.com:80"
https_proxy = "http://proxy.url.com:80"
ftp_proxy   = "http://proxy.url.com:80"

proxyDict = {
              "http"  : http_proxy,
              "https" : https_proxy,
              "ftp"   : ftp_proxy
            }


apps = ['eStore']
metrics = ['Calls per Minute', 'Number of Slow Calls', 'Number of Very Slow Calls', 'Stall Count',
           'Average Response Time (ms)','Errors per Minute']
summetrics = ['Calls per Minute', 'Average Response Time (ms)','Errors per Minute']
metric_path = 'Overall Application Performance|*'
metric_name = ''
prevmetric_name = ''
for app in apps:
    export_header = 'datetime'
    url = 'https://test.saas.appdynamics.com/controller/rest/applications/' + app + '/metric-data?time-range-type=BEFORE_NOW&duration-in-mins=' + str(durationinmins) + '&metric-path=' + metric_path + '&rollup=false&output=JSON'
    resp = requests.get(url, auth=HTTPBasicAuth('user@account', 'pass'),proxies=proxyDict)
    # reader = codecs.getreader("utf-8")
    md_list = json.loads(resp._content.decode('utf-8'))

    freq = freq_to_mins(md_list[0])
    mv = ['--'] * 60
    columnindex = 0
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
                    else:
                        mv = [s + '--' if s.endswith(',') else s for s in mv]
                        mv = [s + ',' for s in mv]
                prevmetric_name = metric_name
                for i in range(0, len(md['metricValues'])):
                    minute_index = int((md['metricValues'][i]['startTimeInMillis'] - start_epoch) / 1000 / 60 / freq)
                    if minute_index >= 0 and minute_index < 60:
                        if mv[minute_index].startswith('--'):
                            mv[minute_index] = str(time.strftime('%m/%d/%y %I:%M:%S %p', time.localtime(
                                md['metricValues'][i]['startTimeInMillis'] / 1000))).replace(' 0', ' ') + ','
                            for j in range(0, columnindex):
                                mv[minute_index] = mv[minute_index] + '--,'
                        mv[minute_index] = mv[minute_index] + str(md['metricValues'][i]['value'])
                        if metric_name in summetrics:
                            mv[minute_index] = mv[minute_index] + ',' + str(md['metricValues'][i]['sum'])
                if metric_name in summetrics:
                    columnindex = columnindex + 2
                else:
                    columnindex = columnindex + 1
    if metric_name in summetrics:
        mv = [s + '--,--' if s.endswith(',') else s for s in mv]
    else:
        mv = [s + '--' if s.endswith(',') else s for s in mv]




    # complete directory path where we need to store the data files
    dir='.'
    # file for each backend is a combination of the backend name & week's Monday date
    filename = dir + '/' + app.replace('/', '') + '_' + week_monday.strftime('%m%d%Y') + '.csv'
    if not os.path.exists(filename):
        f = open(filename, 'a')
        f.write(export_header)
    else:
        f = open(filename, 'a')
    for i in range(0, len(mv)):
        if '--,--,--,--,--,--,--,--,--' != mv[i] and '--,--,--,--,--,--,--,--' != mv[i]:
            f.write('\n')
            f.write(mv[i])
        else:
            if i == 0:
                datetime_prev = (start_time.replace(minute=0, second=0, microsecond=0) - timedelta(seconds=60)).strftime(
                    "%m/%d/%y %I:%M:%S %p")
            else:
                datetime_prev = mv[i - 1].split(",")[0]
            datetime_prev = datetime.strptime(datetime_prev, "%m/%d/%y %I:%M:%S %p") + timedelta(seconds=60)
            mv[i] = datetime.strftime(datetime_prev, '%m/%d/%y %I:%M:%S %p').replace(' 0', ' ') + ',--,--,--,--,--,--,--,--'
            f.write('\n')
            f.write(mv[i])
    f.close()
