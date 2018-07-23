import yaml, json

class YAML(object):
    def __init__(self, data):
        self.data = data

    def _insert(self, instance):
        if type(self.data) == list and type(instance) == list:
            for each in yaml.load(json.dumps(instance)):
                if each not in self.data:
                    self.data.append(each)
        elif type(self.data) == dict and type(instance) == dict:
            self.data.update(yaml.load(json.dumps(instance, encoding="utf-8")))
        else:
            self.data = None
        return YAML(self.data)

    def _delete(self, instance):
        if not self.data:
            return YAML(None)
        if type(self.data) == list and type(instance) == dict:
            flag = False
            for index, elm in enumerate(self.data):
                for key, value in instance.items():
                    if key in elm and elm[key] == value:
                        flag = True
                        break
                if flag:
                    break
            if flag:
                self.data.pop(index)
        elif type(self.data) == dict and type(instance) == list:
            for each in instance:
                if each in self.data:
                    self.data.pop(each)
        else:
            self.data = None
        return YAML(self.data)

    def _filter(self, options):
        if not self.data:
            return YAML(None)
        #if options.find('==') != -1:
        if type(options) == str:
            args = options.split('==')
            for each in self.data:
                if args[0] in each and each[args[0]] == args[1]:
                    return YAML(each)
            return YAML(None)
        elif type(options) == dict:
            if type(self.data) == list:
                for each in self.data:
                    for key, value in options.items():
                        if key in each and each[key] == value:
                            self.data = each
            else:
                self.data = None
            return YAML(self.data)
        elif type(options) == list:
            for each in options:
                if type(self.data) == dict:
                    if each not in self.data:
                        return YAML(None)
                    self.data = self.data[each]
                elif type(self.data) == list:
                    flag = True
                    for elm in self.data:
                        if each in elm:
                            self.data = elm[each]
                            flag = False
                            break
                    if flag:
                        self.data = None
            return YAML(self.data)
            
def getconfig():
    f = open('/tmp/prometheus.yml', 'r')
    ym = yaml.load(f)
    f.close()
    return ym

if __name__ == "__main__":
    #f = open('/tmp/prometheus.yml', 'r')
    f = open('/tmp/rule.yml', 'r')
    ym = yaml.load(f)
    f.close()
    data = YAML(getconfig())._filter(['scrape_configs'])._filter('job_name==snmp')._filter(['static_configs','targets']).data
    print 'data', data
