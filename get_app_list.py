from appd.cmdline import parse_argv
from appd.request import AppDynamicsClient


# Credentials for the Client connection
username = "user"
password = "pass"
baseurl = "https://test.saas.appdynamics.com"
account = "test"

c = AppDynamicsClient(account=account, base_url=baseurl, username=username, password=password)

for app in c.get_applications():
    try: 
        metric_data = c.get_metrics('Overall Application Performance|*', app_id=app.id)
        art = metric_data.by_leaf_name(c.AVERAGE_RESPONSE_TIME).first_value()
        cpm = metric_data.by_leaf_name(c.CALLS_PER_MINUTE).first_value()
        epm = metric_data.by_leaf_name(c.ERRORS_PER_MINUTE).first_value()
        error_pct = round(float(epm) / float(cpm) * 100.0, 1) if cpm > 0 else 0
        print app.id, app.name, art, cpm, epm, error_pct
    except:
        print app.id, app.name, 0,0,0,0
