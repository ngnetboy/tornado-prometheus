
from app.prometheus.handler import Job_SNMP, Config_SNMP, AlertRuleGroups, AlertRuleResources, AlertManagerRoute, AlertManagerGlobal, AlertManagerReceiver, PrometheusGlobal
import tornado


urlpattern = (
    (r'/api/v1/prometheus/job/snmp/?', Job_SNMP),
    (r'/api/v1/prometheus/global/?', PrometheusGlobal),

    (r'/api/v1/prometheus/alert/rules/groups/(?P<name>.*)?', AlertRuleGroups),
    (r'/api/v1/prometheus/alert/rules/resources/(?P<group_name>.*)/(?P<rule_name>.*)?', AlertRuleResources),

    (r'/api/v1/prometheus/alert/manager/route/?', AlertManagerRoute),
    (r'/api/v1/prometheus/alert/manager/global/?', AlertManagerGlobal),
    (r'/api/v1/prometheus/alert/manager/receiver/?', AlertManagerReceiver),

    (r'/api/v1/prometheus/snmp/config/?', Config_SNMP),

)
