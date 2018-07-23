import json

def check_fields(options=None):
    def wapper(func):
        def _wapper(self, **kwargs):
            for key in kwargs:
                kwargs[key] = kwargs[key].encode('utf-8')
            if not options:
                return func(self, **kwargs)

            try:
                if type(self.request.body) == str:
                    body = json.loads(self.request.body)
                else:
                    body = self.request.body
            except Exception, e:
                self.write_message('Please input correct info.')
                raise Exception
            for each in options:
                if each not in body:
                    self.write_message('Please input correct info.')
                    raise Exception
                else:
                    body[each] = body[each].encode('utf-8') if type(body[each]) == unicode else body[each]
            self.request.body = body
            return func(self, **kwargs)
        return _wapper
    return wapper

def encode_field(data):
    if type(data) == dict:
        for key, value in data.items():
            result = encode_field(data[key])
            data[key] = result
    elif type(data) == list:
        for index, value in enumerate(data):
            result = encode_field(value)
            data.pop(index)
            data.insert(index, result)
    elif type(data) == unicode:
        return data.encode('utf-8')
    return data
def encode_fields(options=None):
    def wapper(func):
        def _wapper(self, *args, **kwargs):
            try:
                if type(self.request.body) == str:
                    body = json.loads(self.request.body)
                else:
                    body = self.request.body
            except Exception, e:
                self.write_message('Please input correct info.')
                raise Exception
            for key in kwargs:
                kwargs[key] = kwargs[key].encode('utf-8')
            if options:
                for key in body:
                    if key not in options:
                        self.write_message('Parameter error.')
                        raise Exception
            self.request.body = encode_field(body)
            return func(self, *args, **kwargs)
        return _wapper
    return wapper
