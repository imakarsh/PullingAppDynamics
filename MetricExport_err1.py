import os
from datetime import datetime, timedelta
from time import mktime
import tzlocal
from array import array
from appd.request import AppDynamicsClient


# The report will generate data for the last 2-hour period before the current hour of the current day.
# It needs to be run for every 2 hours using cron. Prefer to run it at even hours so that it runs 0,2,4,..,22 hours
end_time = datetime.now().replace(minute=0, second=0, microsecond=0)
end_epoch = int(mktime(end_time.timetuple())) * 1000
start_time = end_time - timedelta(hours=2)
start_epoch = int(mktime(start_time.timetuple())) * 1000
# Pulls data from Monday to Sunday into a single file for each backend.
week_monday = start_time - timedelta(days=start_time.weekday())

# Credentials for the Client connection
username = "user"
password = "pass"
baseurl = "https://test.saas.appdynamics.com"
account = "test"

c = AppDynamicsClient(account=account, base_url=baseurl, username=username, password=password)

# Add more backend values to create additional backend extracts
backends = ['/RequestCenter/nsapi', 'myservices/executeFormRules.execute']

for backend_value in backends :
    metric_path = 'Business Transaction Performance|Business Transactions|RequestCenter|' + backend_value + '|*'
    export_header = 'datetime'
    md_list = c.get_metrics(metric_path, 'eStore-prod', time_range_type='BETWEEN_TIMES', end_time=end_epoch,
                            start_time=start_epoch, rollup=False)
    mv = [''] * 120
    for md in md_list:
        if len(md.values) > 0:
            # Get the last two components of the metric path. This should be 'backend_name|metric_name'.
            backend_name, metric_name = md.path.split('|')[-2:]
            export_header = export_header + ',' + metric_name
            for i in range(0, 120):
                if '' == mv[i]:
                    mv[i] = str(md.values[i].start_time)
                mv[i] = mv[i] + ',' + str(md.values[i].value)

    # complete directory path where we need to store the data files
    dir='.'
    # file for each backend is a combination of the backend name & week's Monday date
    filename = dir + '/' + backend_name.replace('/', '') + '_' + week_monday.strftime('%m%d%Y') + '.csv'
    if not os.path.exists(filename):
        f = open(filename, 'a')
        f.write(export_header)
    else:
        f = open(filename, 'a')
    for i in range(0, len(mv)):
       f.write('\n')
       f.write(mv[i])
    f.close()