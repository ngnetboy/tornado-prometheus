from tornado.web import RequestHandler
import json


class BaseHandler(RequestHandler):
    
    def write_json(self, data):
        result = {'error':0, 'errormsg':"success", 'data':None}
        result['data'] = data
        self.write(json.dumps(result))
        self.flush(include_footers=True)

    def write_message(self, message):
        data = {'error':0, 'errormsg':"success", 'data':None}
        if message != 'success':
            data['error'] = 1
            data['errormsg'] = message
        self.write(json.dumps(data))
        self.flush(include_footers=True)
            
