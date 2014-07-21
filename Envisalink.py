import asyncore, asynchat
import socket
import logging
import time
import datetime

from envisalinkdefs import evl_ResponseTypes
from envisalinkdefs import evl_Defaults
from envisalinkdefs import evl_ArmModes

ALARMSTATE={'version' : 0.2}

def dict_merge(a, b):
    c = a.copy()
    c.update(b)
    return c

def getMessageType(code):
    return evl_ResponseTypes[code]

def to_chars(string):
    chars = []
    for char in string:
        chars.append(ord(char))
    return chars

def get_checksum(code, data):
    return ("%02X" % sum(to_chars(code)+to_chars(data)))[-2:]

class Client(asynchat.async_chat):
    def __init__(self, config, proxyclients):

        self.logger = logging.getLogger('alarmserver.EnvisalinkClient')

        self.logger.debug('Staring Envisalink Client')
        # Call parent class's __init__ method
        asynchat.async_chat.__init__(self)

        # save dict reference to connected clients
        self._proxyclients = proxyclients

        # alarm sate
        self._alarmstate = ALARMSTATE

        # Define some private instance variables
        self._buffer = []

        # Are we logged in?
        self._loggedin = False

        # Set our terminator to \n
        self.set_terminator("\r\n")

        # Set config
        self._config = config

        # Reconnect delay
        self._retrydelay = 10

        self.do_connect()

    def do_connect(self, reconnect = False):
        # Create the socket and connect to the server
        if reconnect == True:
            self.logger.warning('Connection failed, retrying in '+str(self._retrydelay)+ ' seconds')
            for i in range(0, self._retrydelay):
                time.sleep(1)

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

        self.logger.debug('Connecting to {}:{}'.format(self._config.ENVISALINKHOST, self._config.ENVISALINKPORT))
        self.connect((self._config.ENVISALINKHOST, self._config.ENVISALINKPORT))

    def collect_incoming_data(self, data):
        # Append incoming data to the buffer
        self._buffer.append(data)

    def found_terminator(self):
        line = "".join(self._buffer)
        self.handle_line(line)
        self._buffer = []

    def handle_connect(self):
        self.logger.info("Connected to %s:%i" % (self._config.ENVISALINKHOST, self._config.ENVISALINKPORT))
        pass

    def handle_close(self):
        self._loggedin = False
        self.close()
        self.logger.info("Disconnected from %s:%i" % (self._config.ENVISALINKHOST, self._config.ENVISALINKPORT))
        self.do_connect(True)

    def handle_error(self):
        self._loggedin = False
        self.close()
        self.logger.error("Disconnected from %s:%i" % (self._config.ENVISALINKHOST, self._config.ENVISALINKPORT))
        self.do_connect(True)

    def send_command(self, code, data, checksum = True):
        if checksum == True:
            to_send = code+data+get_checksum(code,data)+'\r\n'
        else:
            to_send = code+data+'\r\n'

        self.logger.debug('TX > '+to_send[:-1])
        self.push(to_send)

    def handle_line(self, input):
        if input != '':
            for client in self._proxyclients:
                self._proxyclients[client].send_command(input, False)

            code=int(input[:3])
            parameters=input[3:][:-2]
            event = getMessageType(int(code))
            message = self.format_event(event, parameters)
            self.logger.debug('RX < ' +str(code)+' - '+message)

            try:
                handler = "handle_%s" % evl_ResponseTypes[code]['handler']
            except KeyError:
                #call general event handler
                self.handle_event(code, parameters, event, message)
                return

            try:
                func = getattr(self, handler)
            except AttributeError:
                raise CodeError("Handler function doesn't exist")

            func(code, parameters, event, message)

    def format_event(self, event, parameters):
        if 'type' in event:
            if event['type'] in ('partition', 'zone'):
                if event['type'] == 'partition':
                    # If parameters includes extra digits then this next line would fail
                    # without looking at just the first digit which is the partition number
                    if int(parameters[0]) in self._config.PARTITIONNAMES:
                        # After partition number can be either a usercode
                        # or for event 652 a type of arm mode (single digit)
                        # Usercode is always 4 digits padded with zeros
                        if len(str(parameters)) == 5:
                            # We have a usercode
                            try:
                                usercode = int(parameters[1:5])
                            except:
                                usercode = 0
                            if int(usercode) in self._config.ALARMUSERNAMES:
                                alarmusername = self._config.ALARMUSERNAMES[int(usercode)]
                            else:
                                # Didn't find a username, use the code instead
                                alarmusername = usercode
                            return event['name'].format(str(self._config.PARTITIONNAMES[int(parameters[0])]), str(alarmusername))
                        elif len(parameters) == 2:
                            # We have an arm mode instead, get it's friendly name
                            armmode = evl_ArmModes[int(parameters[1])]
                            return event['name'].format(str(self._config.PARTITIONNAMES[int(parameters[0])]), str(armmode))
                        else:
                            return event['name'].format(str(self._config.PARTITIONNAMES[int(parameters)]))
                elif event['type'] == 'zone':
                    if int(parameters) in self._config.ZONENAMES:
                        if self._config.ZONENAMES[int(parameters)]!=False:
                            return event['name'].format(str(self._config.ZONENAMES[int(parameters)]))

        return event['name'].format(str(parameters))

    #envisalink event handlers, some events are unhandeled.
    def handle_login(self, code, parameters, event, message):
        if parameters == '3':
            self._loggedin = True
            self.send_command('005', self._config.ENVISALINKPASS)
        if parameters == '1':
            self.send_command('001', '')
        if parameters == '0':
            self.logger.warning('Incorrect envisalink password')
            sys.exit(0)

    def handle_event(self, code, parameters, event, message):
        # only handle events with a 'type' defined
        if not 'type' in event:
            return

        if not event['type'] in self._alarmstate: 
            self._alarmstate[event['type']]={'lastevents' : []}

        # save event in alarm state depending on
        # the type of event

        parameters = int(parameters)

        # if zone event
        if event['type'] == 'zone':
            zone = parameters
            # if the zone is named in the config file save info in self._alarmstate
            if zone in self._config.ZONENAMES:
                # save zone if not already there
                if not zone in self._alarmstate['zone']: 
                    self._alarmstate['zone'][zone] = {'name' : self._config.ZONENAMES[zone]}
            else:
                self.logger.debug('Ignoring unnamed zone {}'.format(zone))

        # if partition event
        elif event['type'] == 'partition':
            partition = parameters
            if partition in self._config.PARTITIONNAMES:
                # save partition name in alarmstate
                if not partition in self._alarmstate['partition']: 
                    self._alarmstate['partition'][partition] = {'name' : self._config.PARTITIONNAMES[partition]}
            else:
                self.logger.debug('Ignoring unnamed partition {}'.format(partition))
        else:
            if not parameters in self._alarmstate[event['type']]: 
                self._alarmstate[event['type']][partition] = {}

        # shorthand to event state
        eventstate = self._alarmstate[event['type']]

        # return if the parameters isn't in the alarm event state
        # i.e. if the current event type is in zone 1 (event[type]:zone, param:1)
        # then, if there isn't an alaramstate['zone'][2], return
        if not parameters in eventstate:
            return

        # populate status with defaults if there isn't already a status
        if not 'status' in eventstate[parameters]:
                eventstate[parameters]['status'] = evl_Defaults[event['type']]

        prev_state = eventstate[parameters]['status']
        # save event status
        if 'status' in event:
            eventstate[parameters]['status']=dict_merge(eventstate[parameters]['status'], event['status'])

        # append event to lastevents, crete list if it doesn't exist
        if not 'lastevents' in eventstate[parameters]: 
            eventstate[parameters]['lastevents'] = []

        # if the state of the alarm (i.e., zone, partition, etc) remains
        # unchanged after event['status'] has been merged, return and
        # do not store in history
        if prev_state == eventstate[parameters]['status']:
            self.logger.debug('Discarded event. State not changed. ({} {})'.format(event['type'], parameters))
            return

        # if lastevents is a list of non-zero length
        if eventstate[parameters]['lastevents']:
            # if this event is the same as previous discard it 
            # except if lastevents is empty, then we get an IndexError exception
            if eventstate[parameters]['lastevents'][-1]['code'] == code:
                self.logger.debug('{}:{} ({}) discarded duplicate event'.format(event['type'], parameters, code))
                return

        # append this event  to lastevents
        eventstate[parameters]['lastevents'].append({  
                  'datetime' : str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), 
                  'code'     : code,
                  'message'  : message})

        # manage last events list if it's > MAXEVENTS
        if len(eventstate[parameters]['lastevents']) > self._config.MAXEVENTS:
            eventstate[parameters]['lastevents'].pop(0)


        eventstate['lastevents'].append({'datetime' : str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), 'message' : message})
        if len(eventstate['lastevents']) > self._config.MAXALLEVENTS:
            eventstate['lastevents'].pop(0)


    def handle_zone(self, code, parameters, event, message):
        self.handle_event(code, parameters[1:], event, message)

    def handle_partition(self, code, parameters, event, message):
        self.handle_event(code, parameters[0], event, message)

class Proxy(asyncore.dispatcher):
    def __init__(self, config, server):

        self.logger = logging.getLogger('alarmserver.Proxy')
        
        self._config = config
        if self._config.ENABLEPROXY == False:
            return

        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.logger.info('Envisalink Proxy Started')

        self.bind(("", self._config.ENVISALINKPROXYPORT))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is None:
            pass
        else:
            sock, addr = pair
            self.logger.info('Incoming proxy connection from %s' % repr(addr))
            handler = ProxyChannel(server, self._config.ENVISALINKPROXYPASS, sock, addr)

