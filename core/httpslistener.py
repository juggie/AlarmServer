#python modules
import os

#tornado modules
import tornado.ioloop
import tornado.web
import tornado.httpserver

#alarm server modules
from .config import config
from .state import state
from .events import events
from .httpslistener_auth import require_basic_auth
from . import logger

@require_basic_auth
class ApiAlarmHandler(tornado.web.RequestHandler):
    def get(self, request):
        parameters = {}
        parameters['alarmcode'] = self.get_argument('alarmcode', None)
        parameters['partition'] = self.get_argument('partition', 1)
        if request == 'arm':
            response = {'response' : 'Request to arm partition %s received' % parameters['partition']}
        elif request == 'stayarm':
            response = {'response' : 'Request to arm partition %s in stay received' % parameters['partition']}
        elif request == 'armwithcode':
            if parameters['alarmcode'] == None: raise tornado.web.HTTPError(404)
            response = {'response' : 'Request to arm partition %s with code received' % parameters['partition']}
        elif request == 'disarm':
            if parameters['alarmcode'] == None: raise tornado.web.HTTPError(404)
            response = {'response' : 'Request to disarm partition %s received' % parameters['partition']}
        elif request == 'refresh':
            response = {'response' : 'Request to refresh data received'}
        elif request == 'pgm':
            response = {'response' : 'Request to trigger PGM'}

        #send event for our request
        events.put('alarm_update', request, parameters)
        self.write(response)

@require_basic_auth
class ApiEventTimeAgoHandler(tornado.web.RequestHandler):
    def get(self):
        self.write({'eventtimeago' : config.EVENTTIMEAGO})

@require_basic_auth
class ApiHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(state.getDict())

@require_basic_auth
class AuthStaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
    def get(self, filename):
        return super(AuthStaticFileHandler, self).get(filename)

def start(https = True):
    if https == True and (not config.CERTFILE or not config.KEYFILE):
        logger.error("Unable to start HTTPS server without certfile and keyfile")
    else:
        logger.info("%s Server started on port: %s" % (('HTTPS',config.HTTPSPORT) if https == True else ('HTTP', config.HTTPPORT))) 
        ext_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../ext')
        return tornado.httpserver.HTTPServer(tornado.web.Application([
            (r'/api/alarm/(arm|stayarm|armwithcode|disarm)', ApiAlarmHandler),
            (r'/api/(refresh|pgm)', ApiAlarmHandler),
            (r'/api/config/eventtimeago', ApiEventTimeAgoHandler),
            (r'/api', ApiHandler),
            (r'/img/(.*)', AuthStaticFileHandler, {'path': ext_path}),
            (r'/(.*)', AuthStaticFileHandler, {'default_filename' : 'index.html', 'path': ext_path}),
        ]),ssl_options={"certfile": config.CERTFILE, "keyfile" : config.KEYFILE} if https == True else None).listen(config.HTTPSPORT if https == True else config.HTTPPORT)
