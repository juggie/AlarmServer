"""Envisalink module"""
#pylint: disable=R0201

import time
import sys
import re
from socket import gaierror
from tornado import gen
import tornado.ioloop
from tornado.tcpclient import TCPClient
from tornado.iostream import StreamClosedError
from .envisalinkdefs import EVL_RESPONSETYPES
from .envisalinkdefs import EVL_DEFAULTS
from .envisalinkdefs import EVL_ARMMODES

from . import logger
from .events import Events


def get_message_type(code):
    """Return message details for message code"""
    return EVL_RESPONSETYPES[code]


def to_chars(string):
    """Return ascii codes for string"""
    chars = []
    for char in string:
        chars.append(ord(char))
    return chars


def get_checksum(code, data):
    """Get Envisalink checksum"""
    return ("%02X" % sum(to_chars(code) + to_chars(data)))[-2:]


class Client(object):
    """Envisalink Client"""

    def __init__(self, config):
        logger.debug('Starting Envisalink Client')

        # Save a copy of the config
        self.config = config

        # Register events for alarmserver requests -> envisalink
        Events.register('alarm_update', self.request_action)

        # Register events for envisalink proxy
        Events.register('envisalink', self.envisalink_proxy)

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
        tornado.ioloop.PeriodicCallback(self.check_connection, 1000).start()

        # Last activity
        self._last_activity = time.time()

    def check_connection(self):
        """Check the envisalink connection with a ping to make sure it's still alive"""
        if (self._last_activity + self.config.envisalinkkeepalive) < time.time():
            Events.put('alarm_update', 'ping')

    @gen.coroutine
    def do_connect(self, reconnect=False):
        """Create the socket and connect to the server"""
        if reconnect:
            logger.warning('Connection failed, retrying in %s seconds' %
                           str(self._retrydelay))
            yield gen.sleep(self._retrydelay)

        while self._connection is None:
            logger.debug('Connecting to {}:{}'.format(
                self.config.envisalinkhost, self.config.envisalinkport))
            try:
                self._connection = yield self.tcpclient.connect(self.config.envisalinkhost,
                                                                self.config.envisalinkport)
                self._connection.set_close_callback(self.handle_close)
            except StreamClosedError:
                # Failed to connect, but got no connection object so we will
                # loop here
                logger.warning(
                    'Connection failed, retrying in %s seconds' % str(self._retrydelay))
                yield gen.sleep(self._retrydelay)
                continue
            except gaierror:
                # Could not resolve host provided, if this is a reconnect
                # will retry, if not, will fail
                if reconnect:
                    logger.warning('Connection failed, unable to resolve hostname %s, '
                                   'retrying in %s seconds'
                                   % (self.config.envisalinkhost, str(self._retrydelay)))
                    yield gen.sleep(self._retrydelay)
                    continue
                else:
                    logger.warning('Connection failed, unable to resolve hostname %s. '
                                   'Exiting due to incorrect hostname.'
                                   % self.config.envisalinkhost)
                    sys.exit(0)

            try:
                line = yield self._connection.read_until(self._terminator)
            except StreamClosedError:
                # In this state, since the connection object isnt none,
                # its going to throw the callback for handle_close so we just bomb out.
                # and let handle_close deal with this
                return

            logger.debug("Connected to %s:%i" % (
                self.config.envisalinkhost, self.config.envisalinkport))
            self.handle_line(line.decode())

    @gen.coroutine
    def handle_close(self):
        """Handle connection closed"""
        self._connection = None
        logger.info("Disconnected from %s:%i" %
                    (self.config.envisalinkhost, self.config.envisalinkport))
        self.do_connect(True)

    @gen.coroutine
    def send_command(self, code, data='', checksum=True):
        """Send envisalink command"""
        if checksum:
            to_send = code + data + get_checksum(code, data) + '\r\n'
        else:
            to_send = code + data + '\r\n'

        try:
            yield self._connection.write(to_send.encode('ascii'))
            logger.debug('TX > ' + to_send[:-1])
        except StreamClosedError:
            # we don't need to handle this, the callback has been set for
            # closed connections.
            pass

    @gen.coroutine
    def handle_line(self, rawinput):
        """Handle line of data from envisalink"""
        self._last_activity = time.time()

        if rawinput == '':
            return

        envis_input = rawinput.strip()
        if self.config.envisalinklograw:
            logger.debug('RX RAW < "' + str(envis_input) + '"')

        if re.match(r'^\d\d:\d\d:\d\d ', envis_input):
            #pylint: disable=W0612
            evltime = envis_input[:8]
            #pylint: enable=W0612
            envis_input = envis_input[9:]

        if not re.match(r'^[0-9a-fA-F]{5,}$', envis_input):
            logger.warning('Received invalid TPI message: ' + repr(rawinput))
            return

        code = int(envis_input[:3])
        parameters = envis_input[3:][:-2]
        try:
            event = get_message_type(int(code))
        except KeyError:
            logger.warning('Received unknown TPI code: "%s", parameters: "%s"' %
                           (envis_input[:3], parameters))
            return

        rcksum = int(envis_input[-2:], 16)
        ccksum = int(get_checksum(envis_input[:3], parameters), 16)
        if rcksum != ccksum:
            logger.warning('Received invalid TPI checksum %02X vs %02X: "%s"' %
                           (rcksum, ccksum, envis_input))
            return

        message = self.format_event(event, parameters)
        logger.debug('RX < ' + str(code) + ' - ' + message)

        try:
            handler = "handle_%s" % event['handler']
        except KeyError:
            handler = "handle_event"

        try:
            func = getattr(self, handler)
            if handler != 'handle_login':
                Events.put('proxy', None, rawinput)
        except AttributeError:
            raise Exception("Handler function doesn't exist")

        func(code, parameters, event, message)
        try:
            line = yield self._connection.read_until(self._terminator)
            self.handle_line(line.decode())
        except StreamClosedError:
            # we don't need to handle this, the callback has been set for
            # closed connections.
            pass

    def format_event(self, event, parameters):
        """Get string representation of event"""
        if 'type' in event:
            if event['type'] == 'partition':
                # If parameters includes extra digits then this next line would fail
                # without looking at just the first digit which is the
                # partition number
                if int(parameters[0]) in self.config.partitionnames:
                    # After partition number can be either a usercode
                    # or for event 652 a type of arm mode (single digit)
                    # Usercode is always 4 digits padded with zeros
                    if len(str(parameters)) == 5:
                        # We have a usercode
                        try:
                            usercode = int(parameters[1:5])
                        except ValueError:
                            usercode = 0
                        if int(usercode) in self.config.alarmusernames:
                            alarmusername = self.config.alarmusernames[int(
                                usercode)]
                        else:
                            # Didn't find a username, use the code instead
                            alarmusername = usercode
                        return event['name'].format(
                            str(self.config.partitionnames[int(parameters[0])]), str(alarmusername))
                    elif len(parameters) == 2:
                        # We have an arm mode instead, get it's friendly name
                        armmode = EVL_ARMMODES[int(parameters[1])]
                        return event['name'].format(
                            str(self.config.partitionnames[int(parameters[0])]), str(armmode))
                    else:
                        return event['name'].format(
                            str(self.config.partitionnames[int(parameters)]))
            elif event['type'] == 'zone':
                if int(parameters) in self.config.zonenames:
                    if self.config.zonenames[int(parameters)] != False:
                        return event['name'].format(str(self.config.zonenames[int(parameters)]))

        return event['name'].format(str(parameters))

    # pylint: disable=W0613
    def handle_login(self, code, parameters, event, message):
        """Handle envisalink login"""
        if parameters == '3':
            self.send_command('005', self.config.envisalinkpass)
        if parameters == '1':
            self.send_command('001')
        if parameters == '0':
            logger.warning('Incorrect envisalink password')
            sys.exit(0)

    def handle_event(self, code, parameters, event, message):
        """Handle envisalink event"""
        # only handle events with a 'type' defined
        if not 'type' in event:
            return

        parameters = int(parameters)

        try:
            default_status = EVL_DEFAULTS[event['type']]
        except IndexError:
            default_status = {}

        if (event['type'] == 'zone' and parameters in self.config.zonenames) or\
                (event['type'] == 'partition' and parameters in self.config.partitionnames):
            Events.put('alarm', event['type'], parameters,
                       code, event, message, default_status)
        elif event['type'] == 'zone' or event['type'] == 'partition':
            logger.debug('Ignoring unnamed %s %s' %
                         (event['type'], parameters))
        else:
            logger.debug('Ignoring unhandled event %s' % event['type'])

    def handle_zone(self, code, parameters, event, message):
        """Handle envisalink zone"""
        self.handle_event(code, parameters[1:], event, message)

    def handle_partition(self, code, parameters, event, message):
        """Handle envisalink partition"""
        self.handle_event(code, parameters[0], event, message)

    def request_action(self, eventtype, type, parameters):
        """Handle envisalink requested action"""
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
                self.send_command('040', partition +
                                  str(parameters['alarmcode']))
            else:
                self.send_command('040', partition +
                                  str(self.config.alarmcode))
        elif type == 'refresh':
            self.send_command('001')
        elif type == 'ping':
            self.send_command('000')
        elif type == 'pgm':
            #TODO: wtf?
            response = {'response': 'Request to trigger PGM'}

    @gen.coroutine
    def envisalink_proxy(self, eventtype, type, parameters, *args):
        """Envisalink proxy"""
        try:
            yield self._connection.write(parameters)
            logger.debug('PROXY > ' + parameters.strip().decode())
        except StreamClosedError:
            # we don't need to handle this, the callback has been set for
            # closed connections.
            pass
