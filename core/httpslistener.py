#python modules
import os

#tornado modules
import tornado.ioloop
import tornado.web
import tornado.httpserver

#alarm server modules
from config import config
from state import state
from events import events
import logger

class ApiAlarmHandler(tornado.web.RequestHandler):
    def get(self, request):
        parameters = {}
        parameters['alarmcode'] = self.get_argument('alarmcode', None)
        if request == 'arm':
            response = {'response' : 'Request to arm received'}
        elif request == 'stayarm':
            response = {'response' : 'Request to arm in stay received'}
        elif request == 'armwithcode':
            if parameters['alarmcode'] == None: raise tornado.web.HTTPError(404)
            response = {'response' : 'Request to arm with code received'}
        elif request == 'disarm':
            if parameters['alarmcode'] == None: raise tornado.web.HTTPError(404)
            response = {'response' : 'Request to disarm received'}
        elif request == 'refresh':
            response = {'response' : 'Request to refresh data received'}
        elif request == 'pgm':
            response = {'response' : 'Request to trigger PGM'}

        #send event for our request
        events.put('alarm_update', request, parameters)
        self.write(response)

class ApiEventTimeAgoHandler(tornado.web.RequestHandler):
    def get(self):
        self.write({'eventtimeago' : config.EVENTTIMEAGO})

class ApiHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(state.getDict())

def start(https = True):
    logger.info("%s Server started on port: %s" % (('HTTPS',config.HTTPSPORT) if https == True else ('HTTP', config.HTTPPORT))) 
    ext_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../ext')
    return tornado.httpserver.HTTPServer(tornado.web.Application([
        (r'/api/alarm/(arm|stayarm|armwithcode|disarm)', ApiAlarmHandler),
        (r'/api/(refresh|pgm)', ApiAlarmHandler),
        (r'/api/config/eventtimeago', ApiEventTimeAgoHandler),
        (r'/api', ApiHandler),
        (r'/img/(.*)', tornado.web.StaticFileHandler, {'path': ext_path}),
        (r'/(.*)', tornado.web.StaticFileHandler, {'default_filename' : 'index.html', 'path': ext_path}),
    ]),ssl_options={"certfile": config.CERTFILE, "keyfile" : config.KEYFILE} if https == True else None).listen(config.HTTPSPORT if https == True else config.HTTPPORT)
