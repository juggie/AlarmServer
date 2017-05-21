"""Alarmserver HTTPListener"""
#pylint: disable=W0221,W0223,W0235
#python modules
import os

#tornado modules
import tornado.ioloop
import tornado.web
import tornado.httpserver

#alarm server modules
from .state import State
from .events import Events
from .httpslistener_auth import require_basic_auth
from . import logger

@require_basic_auth
class ApiAlarmHandler(tornado.web.RequestHandler):
    """Tornado API Handler"""
    def initialize(self, config):
        self.config = config
    def get(self, request):
        parameters = {}
        parameters['alarmcode'] = self.get_argument('alarmcode', None)
        parameters['partition'] = self.get_argument('partition', 1)
        if request == 'arm':
            response = {'response' : 'Request to arm partition %s received'
                                     % parameters['partition']}
        elif request == 'stayarm':
            response = {'response' : 'Request to arm partition %s in stay received'
                                     % parameters['partition']}
        elif request == 'armwithcode':
            if parameters['alarmcode'] is None:
                raise tornado.web.HTTPError(404)
            response = {'response' : 'Request to arm partition %s with code received'
                                     % parameters['partition']}
        elif request == 'disarm':
            if parameters['alarmcode'] is None:
                raise tornado.web.HTTPError(404)
            response = {'response' : 'Request to disarm partition %s received'
                                     % parameters['partition']}
        elif request == 'refresh':
            response = {'response' : 'Request to refresh data received'}
        elif request == 'pgm':
            response = {'response' : 'Request to trigger PGM'}

        #send event for our request
        Events.put('alarm_update', request, parameters)
        self.write(response)

@require_basic_auth
class ApiEventTimeAgoHandler(tornado.web.RequestHandler):
    """Tornado API Timeago Handler"""
    def initialize(self, config):
        self.config = config
    def get(self):
        self.write({'eventtimeago' : self.config.eventtimeago})

@require_basic_auth
class ApiHandler(tornado.web.RequestHandler):
    """Tornado API REST Handler"""
    def initialize(self, config):
        self.config = config
    def get(self):
        self.write(State.get_dict())

@require_basic_auth
class AuthStaticFileHandler(tornado.web.StaticFileHandler):
    """Tornado API Static File Handler"""
    def initialize(self, config):
        self.config = config
    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
    def get(self, filename):
        return super(AuthStaticFileHandler, self).get(filename)

def start(config, https=True):
    """Start HTTP Listener"""
    if https and (not config.certfile or not config.keyfile):
        logger.error("Unable to start HTTPS server without certfile and keyfile")
    else:
        logger.info("%s Server started on port: %s" %
                    (('HTTPS', config.httpsport) if https else ('HTTP', config.httpport)))
        ext_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../ext')
        return tornado.httpserver.HTTPServer(
            tornado.web.Application([
                (r'/api/alarm/(arm|stayarm|armwithcode|disarm)', ApiAlarmHandler,
                 {'config' : config}),
                (r'/api/(refresh|pgm)', ApiAlarmHandler, {'config' : config}),
                (r'/api/Config/eventtimeago', ApiEventTimeAgoHandler, {'config' : config}),
                (r'/api', ApiHandler, {'config' : config}),
                (r'/img/(.*)', AuthStaticFileHandler, {'path': ext_path, 'config' : config}),
                (r'/(.*)', AuthStaticFileHandler, {'default_filename' : 'index.html',
                                                   'path': ext_path, 'config' : config}),
                ]),
            ssl_options={"certfile": config.certfile, "keyfile" : config.keyfile}
            if https else None).listen(config.httpsport if https else config.httpport)
