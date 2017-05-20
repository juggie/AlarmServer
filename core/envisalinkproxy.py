from . import logger

from tornado import gen
from tornado.tcpserver import TCPServer
from tornado.iostream import IOStream, StreamClosedError

from .config import Config
from .events import events
from .envisalink import get_checksum

#TODO: handle exceptions

class Proxy(object):
    def __init__(self):
        if Config.ENABLEPROXY == True:
            logger.debug('Staring Envisalink Proxy')
            proxy = ProxyServer()
            proxy.listen(Config.ENVISALINKPROXYPORT)

class ProxyServer(TCPServer):
    def __init__(self, io_loop=None, ssl_options=None, **kwargs):
        TCPServer.__init__(self, io_loop=io_loop, ssl_options=ssl_options, **kwargs)
        self.connections = {}
        events.register('proxy', self.proxy_event)

    @gen.coroutine
    def handle_stream(self, stream, address):
        connection = ProxyConnection(stream, address)
        fromaddr = "%s:%s" % (address[0], address[1])
        logger.debug('Proxy Connection from: %s' % fromaddr)
        self.connections[fromaddr]=stream
        yield connection.on_connect()
        del self.connections[fromaddr]

    #zone/parameters not used, should fix this to not be passed
    @gen.coroutine
    def proxy_event(self, zone, parameters, input):
        for s,k in list(self.connections.items()):
            yield k.write(input)

class ProxyConnection(object):
    def __init__(self, stream, address):
        self.authenticated = False
        self.stream = stream
        self.address = address
        self.stream.set_close_callback(self.on_disconnect)
        self.send_command('5053')

    @gen.coroutine
    def on_connect(self):
        yield self.dispatch_client()

    @gen.coroutine
    def on_disconnect(self):
        logger.debug('Client: %s:%s disconnected' % (self.address[0], self.address[1]))
        
    @gen.coroutine
    def dispatch_client(self):
        try:
            while True:
                line = yield self.stream.read_until(b'\r\n')
                if self.authenticated == True:
                    events.put('envisalink', None, line) 
                else:
                    if line.strip() == ('005' + Config.ENVISALINKPROXYPASS + get_checksum('005', Config.ENVISALINKPROXYPASS)):
                        logger.info('Proxy User Authenticated')
                        self.authenticated = True
                        self.send_command('5051')
                    else:
                        logger.info('Proxy User Authentication failed')
                        self.send_command('5050')
                        self.stream.close()
        except StreamClosedError:
            #on_disconnect will catch this
            pass

    @gen.coroutine
    def send_command(self, data, checksum = True):
        if checksum == True:
            to_send = data+get_checksum(data, '')+'\r\n'
        else:
            to_send = data+'\r\n'
        logger.debug('PROXY < %s' % to_send.strip())
        yield self.stream.write(to_send)
