
PROMETHEUS_SETTINGS = {
    'prometheus_path' : '/tmp/prometheus.yml',
    'alert_path':'/tmp/alertmanager.yml',
    'rule_path':'/tmp/rule.yml',
    'snmp_path':'/tmp/snmp.yml',

    'prometheus_reload':'http://127.0.0.1:9090/-/reload',
    'alertmanager_reload':'http://127.0.0.1:9093/-/reload',
    'snmp_reload':'http://127.0.0.1:9116/-/reload',

    'localhost':'http://127.0.0.1:9696/',
}

Manufacturer = {
    0 : 'unknown',
    9 : 'cisco',
    11 : 'hp',
    2011 : 'huawei',
    7564 : 'arraynetworks',
    25506 : 'h3c',
}
