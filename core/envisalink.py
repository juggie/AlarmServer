import time, datetime, sys, re
from tornado import gen
from tornado.tcpclient import TCPClient
from tornado.iostream import IOStream, StreamClosedError
from socket import gaierror
from envisalinkdefs import evl_ResponseTypes
from envisalinkdefs import evl_Defaults
from envisalinkdefs import evl_ArmModes

#alarmserver logger
import logger
import tornado.ioloop

#import config
from config import config
from events import events

def getMessageType(code):
    return evl_ResponseTypes[code]

def to_chars(string):
    chars = []
    for char in string:
        chars.append(ord(char))
    return chars

def get_checksum(code, data):
    return ("%02X" % sum(to_chars(code)+to_chars(data)))[-2:]

class Client(object):
    def __init__(self):
        logger.debug('Starting Envisalink Client')

        # Register events for alarmserver requests -> envisalink
        events.register('alarm_update', self.request_action)

        # Register events for envisalink proxy
        events.register('envisalink', self.envisalink_proxy)

        # Create TCP Client
        self.tcpclient = TCPClient()

        # Connection
        self._connection = None

        # Set our terminator to \r\n
        self._terminator = b"\r\n"

        # Reconnect delay
        self._retrydelay = 10

        # Connect to Envisalink
        self.do_connect()

        # Setup timer to refresh envisalink
        tornado.ioloop.PeriodicCallback(self.refresh, config.ENVISALINKKEEPALIVE*1000).start()

    def refresh(self):
        if self._connection:
            events.put('alarm_update', 'ping')

    @gen.coroutine
    def do_connect(self, reconnect = False):
        # Create the socket and connect to the server
        if reconnect == True:
            logger.warning('Connection failed, retrying in %s seconds' % str(self._retrydelay))
            yield gen.sleep(self._retrydelay)

        while self._connection == None:
            logger.debug('Connecting to {}:{}'.format(config.ENVISALINKHOST, config.ENVISALINKPORT))
            try:
                self._connection = yield self.tcpclient.connect(config.ENVISALINKHOST, config.ENVISALINKPORT)
                self._connection.set_close_callback(self.handle_close)
            except StreamClosedError:
                #failed to connect, but got no connection object so we will loop here
                logger.warning('Connection failed, retrying in %s seconds' % str(self._retrydelay))
                yield gen.sleep(self._retrydelay)
                continue
            except gaierror:
                #could not resolve host provided, if this is a reconnect, will retry, if not, will fail
                if reconnect == True:
                    logger.warning('Connection failed, unable to resolve hostname %s, retrying in %s seconds' % (config.ENVISALINKHOST, str(self._retrydelay)))
                    yield gen.sleep(self._retrydelay)
                    continue
                else:
                    logger.warning('Connection failed, unable to resolve hostname %s.  Exiting due to incorrect hostname.' % config.ENVISALINKHOST)
                    sys.exit(0)

            try:
                line = yield self._connection.read_until(self._terminator)
            except StreamClosedError:
                #in this state, since the connection object isnt none, its going to throw the callback for handle_close so we just bomb out.
                #and let handle_close deal with this
                return

            logger.debug("Connected to %s:%i" % (config.ENVISALINKHOST, config.ENVISALINKPORT))
            self.handle_line(line)

    @gen.coroutine
    def handle_close(self):
        self._connection = None
        #logger.info("Disconnected from %s:%i" % (config.ENVISALINKHOST, config.ENVISALINKPORT))
        self.do_connect(True)

    @gen.coroutine    
    def send_command(self, code, data = '', checksum = True):
        if checksum == True:
            to_send = code+data+get_checksum(code,data)+'\r\n'
        else:
            to_send = code+data+'\r\n'

        try:
            res = yield self._connection.write(to_send)
            logger.debug('TX > '+to_send[:-1])
        except StreamClosedError:
            #we don't need to handle this, the callback has been set for closed connections.
            pass

    @gen.coroutine
    def handle_line(self, rawinput):
        if rawinput == '':
            return

        input = rawinput.strip()
        if config.ENVISALINKLOGRAW == True:
            logger.debug('RX RAW < "' + str(input) + '"')

        if re.match(r'^\d\d:\d\d:\d\d ',input):
            evltime = input[:8]
            input = input[9:]

        if not re.match(r'^[0-9a-fA-F]{5,}$', input):
            logger.warning('Received invalid TPI message: ' + repr(rawinput));
            return

        code = int(input[:3])
        parameters = input[3:][:-2]
        try:
            event = getMessageType(int(code))
        except KeyError:
            logger.warning('Received unknown TPI code: "%s", parameters: "%s"' %
                           (input[:3], parameters))
            return

        rcksum = int(input[-2:], 16)
        ccksum = int(get_checksum(input[:3],parameters), 16)
        if rcksum != ccksum:
            logger.warning('Received invalid TPI checksum %02X vs %02X: "%s"' %
                           (rcksum, ccksum, input))
            return

        message = self.format_event(event, parameters)
        logger.debug('RX < ' +str(code)+' - '+message)

        try:
            handler = "handle_%s" % event['handler']
        except KeyError:
            handler = "handle_event"

        try:
            func = getattr(self, handler)
            if handler != 'handle_login':
                events.put('proxy', None, rawinput)
        except AttributeError:
            raise CodeError("Handler function doesn't exist")

        func(code, parameters, event, message)
        try:
            line = yield self._connection.read_until(self._terminator)
            self.handle_line(line)
        except StreamClosedError:
            #we don't need to handle this, the callback has been set for closed connections.
            pass

    def format_event(self, event, parameters):
        if 'type' in event:
            if event['type'] in ('partition', 'zone'):
                if event['type'] == 'partition':
                    # If parameters includes extra digits then this next line would fail
                    # without looking at just the first digit which is the partition number
                    if int(parameters[0]) in config.PARTITIONNAMES:
                        # After partition number can be either a usercode
                        # or for event 652 a type of arm mode (single digit)
                        # Usercode is always 4 digits padded with zeros
                        if len(str(parameters)) == 5:
                            # We have a usercode
                            try:
                                usercode = int(parameters[1:5])
                            except:
                                usercode = 0
                            if int(usercode) in config.ALARMUSERNAMES:
                                alarmusername = config.ALARMUSERNAMES[int(usercode)]
                            else:
                                # Didn't find a username, use the code instead
                                alarmusername = usercode
                            return event['name'].format(str(config.PARTITIONNAMES[int(parameters[0])]), str(alarmusername))
                        elif len(parameters) == 2:
                            # We have an arm mode instead, get it's friendly name
                            armmode = evl_ArmModes[int(parameters[1])]
                            return event['name'].format(str(config.PARTITIONNAMES[int(parameters[0])]), str(armmode))
                        else:
                            return event['name'].format(str(config.PARTITIONNAMES[int(parameters)]))
                elif event['type'] == 'zone':
                    if int(parameters) in config.ZONENAMES:
                        if config.ZONENAMES[int(parameters)]!=False:
                            return event['name'].format(str(config.ZONENAMES[int(parameters)]))

        return event['name'].format(str(parameters))

    #envisalink event handlers, some events are unhandeled.
    def handle_login(self, code, parameters, event, message):
        if parameters == '3':
            self.send_command('005', config.ENVISALINKPASS)
        if parameters == '1':
            self.send_command('001')
        if parameters == '0':
            logger.warning('Incorrect envisalink password')
            sys.exit(0)

    def handle_event(self, code, parameters, event, message):
        # only handle events with a 'type' defined
        if not 'type' in event:
            return

        parameters = int(parameters)
        
        try:
            defaultStatus = evl_Defaults[event['type']]
        except IndexError:
            defaultStatus = {}
        
        if (event['type'] == 'zone' and parameters in config.ZONENAMES) or (event['type'] == 'partition' and parameters in config.PARTITIONNAMES):
            events.put('alarm', event['type'], parameters, code, event, message, defaultStatus) 
        elif (event['type'] == 'zone' or event['type'] == 'partition'):
            logger.debug('Ignoring unnamed %s %s' % (event['type'], parameters))
        else:
            logger.debug('Ignoring unhandled event %s' % event['type'])

    def handle_zone(self, code, parameters, event, message):
        self.handle_event(code, parameters[1:], event, message)

    def handle_partition(self, code, parameters, event, message):
        self.handle_event(code, parameters[0], event, message)

    def request_action(self, eventType, type, parameters):
        try:
            partition = str(parameters['partition'])
        except TypeError:
            partition = None

        if type == 'arm':
            self.send_command('030', partition)
        elif type == 'stayarm':
            self.send_command('031', partition)            
        elif type == 'armwithcode':
            self.send_command('033', partition + str(parameters['alarmcode']))
        elif type == 'disarm':
            if 'alarmcode' in parameters:
                self.send_command('040', partition + str(parameters['alarmcode']))
            else:
                self.send_command('040', partition + str(config.ALARMCODE))
        elif type == 'refresh':
            self.send_command('001')
        elif type == 'ping':
            self.send_command('000')
        elif type == 'pgm':
            response = {'response' : 'Request to trigger PGM'}

    @gen.coroutine
    def envisalink_proxy(self, eventType, type, parameters, *args):
        try:
            res = yield self._connection.write(parameters)
            logger.debug('PROXY > '+parameters.strip())
        except StreamClosedError:
            #we don't need to handle this, the callback has been set for closed connections.
            pass

