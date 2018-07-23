from setting import PROMETHEUS_SETTINGS, Manufacturer
from lib.libyaml import YAML
from tornado import gen, httpclient
from lib.supernmslog import aninfo, anexception, andebug, anerror
import copy, yaml

class File(object):
    """
    def __init__(self, file_path, mode):
        self.file_path = file_path
        self.mode = mode
    """

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

class ConfigFile(object):
    def __init__(self):
        self.init_content = ""
        self.url = ""
        self.path = ""

    def get_config(self):
        config_content = File.open_read(self.path, 'r')
        if not config_content:
            return {'error':1, 'message':'Open config file failed.'}
        self.init_content = copy.deepcopy(config_content)
        return {'error':0, 'data':config_content}

    @gen.coroutine
    def write_config(self, data):
        if File.open_write(self.path, 'w', data):
            ret =  yield self.reload_config()
            if ret and '500' in ret:
                File.open_write(self.path, 'w', self.init_content)
                raise gen.Return({'error':1, 'message':'Please input the correct config.'})
            elif ret:
                File.open_write(self.path, 'w', self.init_content)
                raise gen.Return({'error':1, 'message':'Prometheus down.'})
            else:
                raise gen.Return({'error':0})
        else:
            raise gen.Return({'error': 1, 'message':'Write config file failed.'})

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

class PrometheusConfig(ConfigFile):
    def __init__(self):
        super(PrometheusConfig, self).__init__()
        self.url = PROMETHEUS_SETTINGS['prometheus_reload']
        self.path = PROMETHEUS_SETTINGS['prometheus_path']

    
    def get_job_snmp(self):
        config = self.get_config()
        if config['error']:
            return config
        static_config = YAML(config['data'])._filter(['scrape_configs'])._filter('job_name==snmp')._filter(['static_configs']).data
        result = []
        for each in static_config:
            result.append({'module':each['labels']['__param_module'], 'device':each['targets']})
        return {'error':0, 'data':result}       

    def get_specify_module(self, data, module):
        if type(data) != list:
            return None
        for each in data:
            if each['labels']['__param_module'] == module:
                return each
        return None

    @gen.coroutine
    def post_job_snmp(self, body):
        config = self.get_config()
        if config['error']:
            raise gen.Return(config)

        config_data = config['data']

        static_config = YAML(config_data)._filter(['scrape_configs'])._filter('job_name==snmp')._filter(['static_configs'])

        if body['module'] not in Manufacturer:
            raise gen.Return({'error':1, 'message':'Unknown device type.'})
        module = Manufacturer[body['module']]
        if self.get_specify_module(static_config.data, module):
            raise gen.Return({'error':1, 'message':'This module has existed.'})

        post_config = [{
            "targets": body['device_list'],
            "labels": {"__param_module": module}
        }]

        data = static_config._insert(post_config).data
        if not data:
            raise gen.Return({'error':1, 'message':'Set config failed.'})
        result = yield self.write_config(config_data)
        raise gen.Return(result)

    @gen.coroutine
    def put_job_snmp(self, body):
        config = self.get_config()
        if config['error']:
            raise gen.Return(config)

        config_data = config['data']

        static_config = YAML(config_data)._filter(['scrape_configs'])._filter('job_name==snmp')._filter(['static_configs'])

        if body['module'] not in Manufacturer:
            raise gen.Return({'error':1, 'message':'Unknown device type.'})
        module = Manufacturer[body['module']]
        module_config = self.get_specify_module(static_config.data, module)
        if not module_config:
            raise gen.Return({'error':1, 'message':'This module has not existed.'})

        data = static_config._filter({'labels':module_config['labels']})._insert({'targets':body['device_list']}).data

        if not data:
            raise gen.Return({'error':1, 'message':'Update config failed.'})
        result = yield self.write_config(config_data)
        raise gen.Return(result)

    @gen.coroutine
    def delete_job_snmp(self, body):
        config = self.get_config()
        if config['error']:
            raise gen.Return(config)

        config_data = config['data']

        static_config = YAML(config_data)._filter(['scrape_configs'])._filter('job_name==snmp')._filter(['static_configs'])

        if body['module'] not in Manufacturer:
            raise gen.Return({'error':1, 'message':'Unknown device type.'})

        module = Manufacturer[body['module']]
        module_config = self.get_specify_module(static_config.data, module)
        if not module_config :
            raise gen.Return({'error':1, 'message':'This module has not existed in prometheus config file.'})

        module_config.pop('targets')
        data = static_config._delete(module_config).data
        # if not data:
        #     raise gen.Return({'error':1, 'message':'Delete config failed.'})

        result = yield self.write_config(config_data)
        raise gen.Return(result)       

    @gen.coroutine
    def update_global_config(self, body):
        config = self.get_config()
        if config['error']:
            raise gen.Return(config)

        config_data = config['data']

        global_config = YAML(config_data)._filter(['global'])
        data = global_config._insert(body).data
        if not data:
            raise gen.Return({'error':1, 'message':'Update into prometheus config file failed.'})
        result = yield self.write_config(config_data)
        raise gen.Return(result)         

class SNMPConfig(ConfigFile):
    def __init__(self):
        super(SNMPConfig, self).__init__()
        self.url = PROMETHEUS_SETTINGS['snmp_reload']
        self.path = PROMETHEUS_SETTINGS['snmp_path']

    @gen.coroutine
    def update_community(self, community, module):
        config = self.get_config()
        if config['error']:
            raise gen.Return(config)

        config_data = config['data'] 

        try:
            module = module if type(module) == str else Manufacturer[module]
        except Exception, e:
            raise gen.Return({'error':1, 'message':'Unknow device type.'})
        if module not in config_data.keys():
            raise gen.Return({'error':1, 'message':'This module has not existed in snmp config file.'})

        if 'auth' in config_data:
            auth = {'community':community}
            config_data[module]['auth'].update(auth)
        else:
            auth = {'auth':{'community':community}}
            config_data[module].update(auth)               
        result = yield self.write_config(config_data)
        raise gen.Return(result)         

    def get_snmp_config(self, body):
        config = self.get_config()
        if config['error']:
            raise gen.Return(config)

        config_data = config['data'] 

        result = {}
        for module in config_data:
            if 'module' in body and body['module'][0] != module:
                continue
            result[module] = []
            for metric in config_data[module]['metrics']:
                if 'name' in body and body['name'][0] != metric['name']:
                    continue
                result[module].append({'name':metric['name'], 'oid':metric['oid']})
        return {'error':0, 'data':result}  



class RuleConfig(ConfigFile):
    def __init__(self):
        super(RuleConfig, self).__init__()
        self.url = PROMETHEUS_SETTINGS['prometheus_reload']
        self.path = PROMETHEUS_SETTINGS['rule_path']

    def get_rule_resource(self, group_name, rule_name):
        config = self.get_config()
        if config['error']:
            return config

        config_data = config['data']     

        if rule_name:
            data = YAML(config_data)._filter(['groups'])._filter('name==%s' % group_name)._filter(['rules'])._filter('alert==%s' % rule_name).data
        else:
            data = YAML(config_data)._filter(['groups'])._filter('name==%s' % group_name)._filter(['rules']).data
        return {'error':0, 'data':data}   

    @gen.coroutine
    def post_rule_resource(self, group_name, rule_name, body):
        config = self.get_config()
        if config['error']:
            raise gen.Return(config)

        config_data = config['data']    

        group_config = YAML(config_data)._filter(['groups'])._filter('name==%s' % group_name)
        if not group_config.data:
            raise gen.Return({'error':1, 'message':'Group name is not exists in rule config file.'})
            #return self.write_message('Group name is not exists.')

        rules_list = group_config._filter(['rules'])

        if rules_list._filter('alert==%s' % body['alert']).data:
            raise gen.Return({'error':1, 'message':'The rule has existed in rule config file.'})
            #return self.write_message('')

        rule_config = {
            "alert" : body['alert'],
            "expr" : body['expr'],
            "for" : body['for'],
            "labels": {"severity":body['severity']},
            "annotations" : {"description":body['description']}
        }
        data = rules_list._insert([rule_config]).data
        if not data:
            raise gen.Return({'error':1, 'message':'Insert config to rule config file failed.'})
            #return self.write_message('Insert failed.')
        result = yield self.write_config(config_data)
        raise gen.Return(result)              

    @gen.coroutine
    def delete_rule_resource(self, group_name, rule_name):
        config = self.get_config()
        if config['error']:
            raise gen.Return(config)

        config_data = config['data']  

        rules_list = YAML(config_data)._filter(['groups'])._filter('name==%s' % group_name)._filter(['rules'])  
        data = rules_list._delete({'alert':rule_name}).data    
        # if not data:
        #     raise gen.Return({'error':1, 'message':'Delete config from rule config file failed.'}) 

        result = yield self.write_config(config_data)
        raise gen.Return(result)  

    @gen.coroutine
    def put_rule_resource(self, group_name, rule_name, body):
        config = self.get_config()
        if config['error']:
            raise gen.Return(config)

        config_data = config['data']  

        group_config = YAML(config_data)._filter(['groups'])._filter('name==%s' % group_name)
        if not group_config.data:
            raise gen.Return({'error':1, 'message':'Group name is not exists in rule config file.'}) 

        rule = group_config._filter(['rules'])._filter('alert==%s' % rule_name)
        if not rule.data:
            raise gen.Return({'error':1, 'message':'The rule has not existed in rule config file.'}) 

        if 'description' in body:
            body['annotations'] = {'description':body['description']}
            del body['description']
        if 'severity' in body:
            body['labels'] = {'severity':body['severity']}
            del body['severity']

        data = rule._insert(body)
        if not data:
            raise gen.Return({'error':1, 'message':'Update into rule config file failed.'}) 
        result = yield self.write_config(config_data)
        raise gen.Return(result)               

    def get_rule_groups(self, name):
        config = self.get_config()
        if config['error']:
            return config

        config_data = config['data']   

        if name:
            groups = YAML(config_data)._filter(['groups'])._filter('name==%s' % name).data
        else:
            groups = YAML(config_data)._filter(['groups']).data    
        return {'error':0, 'data':groups}      

    @gen.coroutine
    def add_rule_group(self, name):
        config = self.get_config()
        if config['error']:
            raise gen.Return(config)

        config_data = config['data']     

        group = [{'name':name, 'rules':[]}]
        filter_data = YAML(config_data)._filter(['groups'])
        if filter_data._filter('name==%s' % name).data:
            raise gen.Return({'error':1, 'message':'The group has existed in rule config file.'}) 
            
        data = filter_data._insert(group).data
        if not data:
            raise gen.Return({'error':1, 'message':'Insert config into rule config file failed.'}) 
        result = yield self.write_config(config_data)
        raise gen.Return(result)      

    @gen.coroutine
    def delete_rule_group(self, name):
        config = self.get_config()
        if config['error']:
            raise gen.Return(config)

        config_data = config['data']   

        data = YAML(config_data)._filter(['groups'])._delete({'name':name})
        result = yield self.write_config(config_data)
        raise gen.Return(result)                

class AlertManageConfig(ConfigFile):
    def __init__(self):
        super(AlertManageConfig, self).__init__()
        self.url = PROMETHEUS_SETTINGS['alertmanager_reload']
        self.path = PROMETHEUS_SETTINGS['alert_path']
    
    def get_alert_manage_route(self):
        config = self.get_config()
        if config['error']:
            return config

        config_data = config['data']    
        data = YAML(config_data)._filter(['route']).data    
        return {'error':0, 'data':data}         

    @gen.coroutine
    def update_alert_manage_route(self, body):
        config = self.get_config()
        if config['error']:
            raise gen.Return(config)

        config_data = config['data']  

        data = YAML(config_data)._filter(['route'])._insert(body).data
        if not data:
            raise gen.Return({'error':1, 'message':'Update into alert manager config file failed.'}) 
        result = yield self.write_config(config_data)
        raise gen.Return(result)   

    @gen.coroutine
    def update_alert_manage_global(self, body):
        config = self.get_config()
        if config['error']:
            raise gen.Return(config)

        config_data = config['data']  

        data = YAML(config_data)._filter(['global'])._insert(body).data
        if not data:
            raise gen.Return({'error':1, 'message':'Update into alert manager config file failed.'}) 
        result = yield self.write_config(config_data)
        raise gen.Return(result)  

    @gen.coroutine
    def update_alert_manage_receiver(self, body):
        config = self.get_config()
        if config['error']:
            raise gen.Return(config)

        config_data = config['data']  

        data = YAML(config_data)._filter(['receivers'])._filter('name==defaultreceiver')
        if not data.data:
            raise gen.Return({'error':1, 'message':'The defaultreceiver has not existed in alert manage config file.'}) 
            #return self.write_message('The defaultreceiver has not existed.')
        config_result = []
        for each in body:
            if 'receiver' not in each or 'subject' not in each:
                raise gen.Return({'error':1, 'message':'Please input the correct info.'}) 
                #return self.write_message('Please input the correct info.')
            config_result.append({
            'to': each['receiver'],
            'headers':{'subject':each['subject']}
            })

        if not config_result:
            raise gen.Return({'error':1, 'message':'Please input the correct info.'}) 
        data = data._insert({'email_configs':config_result}).data
        if not data:
            raise gen.Return({'error':1, 'message':'Update into alert manager config file failed.'}) 
        result = yield self.write_config(config_data)
        raise gen.Return(result)                