from appd.request import AppDynamicsClient

usr="User"
pwd="pass"

#url="https://test.saas.appdynamics.com/controller/rest/applications?output=json"
#   #"/eStore-prod/metric-data?metric-path=Business%20Transaction%20Performance%7CBusiness%20Transactions%7CServiceLink%7CEndpointMessageListener%3AISEEInboundQueue%7C95th%20Percentile%20Response%20Time%20%28ms%29&time-range-type=BEFORE_NOW&duration-in-mins=15&output=JSON"


c= AppDynamicsClient(account="test",base_url="https://test.saas.appdynamics.com",username=usr,password=pwd)

# for app in c.get_applications():
#     print app.id, app.name

metrics = c.get_metrics(metric_path='Business Transaction Performance|Business Transactions|ECommerce Server',
                        app_id='22',
                        time_range_type='BEFORE_NOW',
                        duration_in_mins=60,
                        rollup=False)
print(len(metrics))

for point in metrics[0].values:
    print(point.start_time, 'Average Response Time: ', point.value)