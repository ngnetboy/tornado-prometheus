from supernms.handler import BaseHandler
from setting import PROMETHEUS_SETTINGS, Manufacturer
from lib.libyaml import YAML
from lib.decorator import encode_fields, check_fields
from lib.supernmslog import aninfo, anexception, andebug, anerror
from tornado import gen, httpclient
from document import PrometheusConfig, SNMPConfig, RuleConfig, AlertManageConfig
import yaml, json, copy
import time

"""
class File(object):
    @staticmethod
    def open_read(file_path, mode):
        try:    
            with open(file_path, mode) as f:
                content = yaml.load(f.read())
        except Exception, e:
            anexception(e)
            return False
        return content

    @staticmethod
    def open_write(file_path, mode, data):
        try:
            with open(file_path, mode) as f:
                f.write(yaml.dump(data))
        except Exception, e:
            anexception(e)
            return False
        return True
class ConfigFile(BaseHandler):
    def initialize(self):
        self.init_content = ""
        self.url = ""
    def get_config(self):
        config_content = File.open_read(self.path, 'r')
        if not config_content:
            self.write_message('Open config file failed.')
            raise Exception
        self.init_content = copy.deepcopy(config_content)
        return config_content
    @gen.coroutine
    def write_config(self, data):
        if File.open_write(self.path, 'w', data):
            ret =  yield self.reload_config()
            if ret and '500' in ret:
                File.open_write(self.path, 'w', self.init_content)
                self.write_message('Please input the correct config.')
            elif ret:
                File.open_write(self.path, 'w', self.init_content)
                self.write_message('Prometheus down.')
            else:
                self.write_message('success')
        else:
            self.write_message('Write config file failed.')

    @gen.coroutine 
    def reload_config(self):
        try:
            http_client = httpclient.AsyncHTTPClient()
            #Body must not be None for method POST
            response = yield http_client.fetch(self.url, method='POST', body='{"a":"a"}')
        #except httpclient.HTTPError as e:
        except Exception as e:
            anexception(e)
            raise gen.Return(str(e))
"""                
class AlertRuleResources(BaseHandler):
    def initialize(self):
        self.rc = RuleConfig()
    @check_fields()
    def get(self, group_name, rule_name):
        result = self.rc.get_rule_resource(group_name, rule_name)
        if result['error']:
            self.write_message(result['message'])
        else:
            self.write_json(result['data'])

    @check_fields(['alert', 'expr', 'for', 'description', 'severity'])
    @gen.coroutine
    def post(self, group_name, rule_name):
        aninfo('Post config to AlertRule Resource : %s - %s' % (group_name, json.dumps(self.request.body)))

        result = yield self.rc.post_rule_resource(group_name, rule_name, self.request.body)
        if result['error']:
            self.write_message(result['message'])
        else:
            self.write_message('success')

    @encode_fields(['alert', 'description', 'expr', 'for', 'severity'])
    @gen.coroutine
    def put(self, group_name, rule_name):
        if not rule_name:
            self.write_message('Please input the rule_name.')
            raise Exception('rule_name is none.')

        aninfo('Put config to AlertRule Resource : %s - %s' % (group_name, json.dumps(self.request.body)))
        result = yield self.rc.put_rule_resource(group_name, rule_name, self.request.body)
        if result['error']:
            self.write_message(result['message'])
        else:
            self.write_message('success')

    @check_fields()
    @gen.coroutine
    def delete(self, group_name, rule_name):
        if not rule_name:
            self.write_message('Please input the rule_name.')
            raise Exception("rule_name is none.")

        aninfo('Delete AlertRule Resource : %s/%s' % (group_name, rule_name))
        result = yield self.rc.delete_rule_resource(group_name, rule_name)
        if result['error']:
            self.write_message(result['message'])
        else:
            self.write_message('success')        
        
class AlertRuleGroups(BaseHandler):
    def initialize(self):
        self.rc = RuleConfig()
    @check_fields()
    def get(self, name):
        result = self.rc.get_rule_groups(name)
        if result['error']:
            self.write_message(result['message'])
        else:
            self.write_json(result['data'])     

    @check_fields()
    @gen.coroutine
    def post(self, name):
        """
        {'name':'name'}
        """

        if not name:
            self.write_message('Please input the group name.')
            raise Exception("group name is none.")
        aninfo('Post config to AlertRule Group : %s' % name)
        result = yield self.rc.add_rule_group(name)
        if result['error']:
            self.write_message(result['message'])
        else:
            self.write_message('success')           

    @check_fields()
    @gen.coroutine
    def delete(self, name):
        if not name:
            self.write_message('Please input the group name.')
            raise Exception("group name is none.")

        aninfo('Delete AlertRule Group : %s' % name)
        result = yield self.rc.delete_rule_group(name)
        if result['error']:
            self.write_message(result['message'])
        else:
            self.write_message('success')  

class PrometheusGlobal(BaseHandler):
    def initialize(self):
        self.pc = PrometheusConfig()

    @encode_fields(['evaluation_interval', 'scrape_interval'])
    @gen.coroutine
    def put(self):
        aninfo('Put config to Prometheus Global : %s' % json.dumps(self.request.body))
        
        result = yield self.pc.update_global_config(self.request.body)
        if result['error']:
            self.write_message(result['message'])
        else:
            self.write_message('success')   
            
class Job_SNMP(BaseHandler):
    def initialize(self):
        self.pc = PrometheusConfig()
        self.sc = SNMPConfig()

    def get(self):
        result = self.pc.get_job_snmp()
        if result['error']:
            self.write_message(result['message'])
        else:
            self.write_json(result['data'])

    @gen.coroutine
    @check_fields(['device_list', 'module'])
    @encode_fields()
    def post(self):
        aninfo('Post Job SNMP : %s' % json.dumps(self.request.body))
        message = ''

        body = self.request.body
        result_job = yield self.pc.post_job_snmp(body)
        if result_job['error']:
            message += result_job['message']

        if not message and 'community' in body:
            result_snmp = yield self.sc.update_community(body['community'], body['module'])

            if result_snmp['error']:
                message += result_snmp['message']
        
        if message:
            self.write_message(message)
        else:
            self.write_message('success')

    @check_fields(['device_list', 'module'])
    @encode_fields()
    @gen.coroutine
    def put(self):
        aninfo('Put Job SNMP : %s' % json.dumps(self.request.body))
        result = yield self.pc.put_job_snmp(self.request.body)
        if result['error']:
            self.write_message(result['message'])
        else:
            self.write_message('success')

    @check_fields(['module'])
    @encode_fields()
    @gen.coroutine
    def delete(self):
        aninfo('Delete Job SNMP : %s' % json.dumps(self.request.body))
        result = yield self.pc.delete_job_snmp(self.request.body)
        if result['error']:
            self.write_message(result['message'])
        else:
            self.write_message('success')
            
class AlertManagerRoute(BaseHandler):
    def initialize(self):
        self.amc = AlertManageConfig()

    def get(self):
        result = self.amc.get_alert_manage_route()
        if result['error']:
            self.write_message(result['message'])
        else:
            self.write_json(result['data'])

    @encode_fields(['group_interval', 'group_wait', 'repeat_interval'])
    @gen.coroutine
    def put(self):
        aninfo('Put config to AlertManager Route : %s' % json.dumps(self.request.body))
        result = yield self.amc.update_alert_manage_route(self.request.body)
        if result['error']:
            self.write_message(result['message'])
        else:
            self.write_message('success')

class AlertManagerGlobal(BaseHandler):
    def initialize(self):
        self.amc = AlertManageConfig()
    @encode_fields(['smtp_smarthost', 'smtp_from', 'smtp_auth_username', 'smtp_auth_password', 'smtp_require_tls'])
    @gen.coroutine
    def put(self):
        log_config = copy.copy(self.request.body)
        if 'smtp_auth_password' in log_config:
            log_config['smtp_auth_password'] = 'xxxxx'
        aninfo('Put config to AlertManager Global : %s' % json.dumps(log_config))
        result = yield self.amc.update_alert_manage_global(self.request.body)
        if result['error']:
            self.write_message(result['message'])
        else:
            self.write_message('success')

class AlertManagerReceiver(BaseHandler):
    def initialize(self):
        self.amc = AlertManageConfig()
    @encode_fields()
    @gen.coroutine
    def put(self):
        aninfo('Put config to AlertManager Receiver : %s' % json.dumps(self.request.body))
        result = yield self.amc.update_alert_manage_receiver(self.request.body)
        if result['error']:
            self.write_message(result['message'])
        else:
            self.write_message('success')

class Config_SNMP(BaseHandler):
    def initialize(self):
        self.sc = SNMPConfig()    
    def get(self):
        args = self.request.query_arguments

        result = self.sc.get_snmp_config(args)
        if result['error']:
            self.write_message(result['message'])
        else:
            self.write_json(result['data'])

    #@check_fields(['module', 'oid', 'name', 'type', 'help'])
    # @check_fields(['module'])
    # @encode_fields()
    # def post(self):
    #     body = self.request.body
    #     config = self.get_config()
            
    #     module = body['module']
    #     if module in config.keys():
    #         return self.write_message('This module has existed.')
    #     include = []
    #     if 'include' in body:
    #         include = body['include']
    #         for item in include:
    #             if item not in Manufacturer:
    #                 return self.write_message('%s is undefined.' % item)
    #     include.append('default')
    #     module_config = {module:{'include':include, 'walk':[], 'metrics':[]}}

    #     data = YAML(config)._insert(module_config)       
    #     if not data:
    #         return self.write_message('Set config failed.')
    #     return self.write_config(config)

    @check_fields(['module'])
    @encode_fields()
    @gen.coroutine
    def put(self):
        body = self.request.body
        try:
            module = body['module'] if type(body['module']) == str else Manufacturer[body['module']]
        except Exception, e:
            self.write_message('Unknow device type')
            raise Exception('Unknow device type.')

        aninfo('Put config snmp : %s' % json.dumps(self.request.body))

        if 'community' in body:
            result = yield self.sc.update_community(body['community'], module)
            if result['error']:
                self.write_message(result['message'])
                raise Exception('update community failed.')
        self.write_message('success')   




