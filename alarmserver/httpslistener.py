#python modules
import os

#tornado modules
import tornado.ioloop
import tornado.web
import tornado.httpserver

#alarm server modules
from config import config
import logger

#TODO: make this much less lame
ALARMCLIENT = None

class ApiAlarmHandler(tornado.web.RequestHandler):
    global ALARMCLIENT
    def get(self, specific):
        parameters = {}
        parameters['alarmcode'] = self.get_argument('alarmcode', None)
        if specific == 'arm':
            response = {'response' : 'Request to arm received'}
        elif specific == 'stayarm':
            response = {'response' : 'Request to arm in stay received'}
        elif specific == 'armwithcode':
            if parameters['alarmcode'] == None: raise tornado.web.HTTPError(404)
            response = {'response' : 'Request to arm with code received'}
        elif specific == 'disarm':
            if parameters['alarmcode'] == None: raise tornado.web.HTTPError(404)
            response = {'response' : 'Request to disarm received'}
        elif specific == 'refresh':
            response = {'response' : 'Request to refresh data received'}
        elif specific == 'pgm':
            response = {'response' : 'Request to trigger PGM'}

        ALARMCLIENT.request_action(specific, parameters)
        self.write(response)

class ApiEventTimeAgoHandler(tornado.web.RequestHandler):
    def get(self):
        global ALARMCLIENT
        self.write({'eventtimeago' : config.EVENTTIMEAGO})

class ApiHandler(tornado.web.RequestHandler):
    def get(self):
        global ALARMCLIENT
        self.write(ALARMCLIENT._alarmstate)

def start(alarmclient):
    global ALARMCLIENT
    ALARMCLIENT = alarmclient
    logger.info("HTTP Server started on port: %s" % config.HTTPSPORT) 
    ext_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../ext')
    return tornado.httpserver.HTTPServer(tornado.web.Application([
        (r'/api/alarm/(arm|stayarm|armwithcode|disarm)', ApiAlarmHandler),
        (r'/api/(refresh|pgm)', ApiAlarmHandler),
        (r'/api/config/eventtimeago', ApiEventTimeAgoHandler),
        (r'/api', ApiHandler),
        (r'/img/(.*)', tornado.web.StaticFileHandler, {'path': ext_path}),
        (r'/(.*)', tornado.web.StaticFileHandler, {'default_filename' : 'index.html', 'path': ext_path}),
    ]),ssl_options={"certfile": config.CERTFILE, "keyfile" : config.KEYFILE}).listen(config.HTTPSPORT)

