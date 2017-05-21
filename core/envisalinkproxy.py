"""Envisalink Proxy"""
#pylint: disable=R0903
from tornado import gen
from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError

from . import logger
from .events import Events
from .envisalink import get_checksum

class Proxy(object):
    """Proxy"""
    def __init__(self, config):
        self.config = config
        if self.config.enableproxy:
            logger.debug('Staring Envisalink Proxy')
            proxy = ProxyServer(self.config)
            proxy.listen(self.config.envisalinkproxyport)

class ProxyServer(TCPServer):
    """ProxyServer"""
    def __init__(self, config, io_loop=None, ssl_options=None, **kwargs):
        TCPServer.__init__(self, io_loop=io_loop, ssl_options=ssl_options, **kwargs)
        self.config = config
        self.connections = {}
        Events.register('proxy', self.proxy_event)

    @gen.coroutine
    def handle_stream(self, stream, address):
        connection = ProxyConnection(self.config, stream, address)
        fromaddr = "%s:%s" % (address[0], address[1])
        logger.debug('Proxy Connection from: %s' % fromaddr)
        self.connections[fromaddr] = stream
        yield connection.on_connect()
        del self.connections[fromaddr]

    #zone/parameters not used, should fix this to not be passed
    @gen.coroutine
    def proxy_event(self, zone, parameters, input):
        """Proxy Event"""
        for s, k in list(self.connections.items()):
            yield k.write(input)

class ProxyConnection(object):
    """ProxyConnection Class"""
    def __init__(self, config, stream, address):
        self.config = config
        self.authenticated = False
        self.stream = stream
        self.address = address
        self.stream.set_close_callback(self.on_disconnect)
        self.send_command('5053')

    @gen.coroutine
    def on_connect(self):
        """On Connect Event"""
        yield self.dispatch_client()

    @gen.coroutine
    def on_disconnect(self):
        """On Disconnect Event"""
        logger.debug('Client: %s:%s disconnected' % (self.address[0], self.address[1]))

    @gen.coroutine
    def dispatch_client(self):
        """Dispatch Client"""
        try:
            while True:
                line = yield self.stream.read_until(b'\r\n')
                if self.authenticated:
                    Events.put('envisalink', None, line)
                else:
                    if line.strip() == '005{}{}'.format(
                            self.config.envisalinkproxypass,
                            get_checksum('005', self.config.envisalinkproxypass)):
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
    def send_command(self, data, checksum=True):
        """Send envisalink command"""
        if checksum:
            to_send = data+get_checksum(data, '')+'\r\n'
        else:
            to_send = data+'\r\n'
        logger.debug('PROXY < %s' % to_send.strip())
        yield self.stream.write(to_send)
