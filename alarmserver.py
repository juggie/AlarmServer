## Alarm Server
## Supporting Envisalink 2DS/3
## Written by donnyk+envisalink@gmail.com
##
## This code is under the terms of the GPL v3 license.


import asyncore, asynchat
import ConfigParser
import datetime
import os, socket, string, sys, httplib, urllib, urlparse, ssl
import StringIO, mimetools
import json
import hashlib
import time

from envisalinkdefs import evl_ResponseTypes
from envisalinkdefs import evl_Defaults
from envisalinkdefs import evl_ArmModes

class CodeError(Exception): pass

ALARMSTATE={'version' : 0.1}
MAXPARTITIONS=16
MAXZONES=128
MAXALARMUSERS=47
CONNECTEDCLIENTS={}

def dict_merge(a, b):
    c = a.copy()
    c.update(b)
    return c

def getMessageType(code):
    return evl_ResponseTypes[code]

def alarmserver_logger(message, type = 0, level = 0):
    print (str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+' '+message)

def to_chars(string):
    chars = []
    for char in string:
        chars.append(ord(char))
    return chars

def get_checksum(code, data):
    return ("%02X" % sum(to_chars(code)+to_chars(data)))[-2:]

#currently supports pushover notifications, more to be added
#including email, text, etc.
#to be fixed!
def send_notification(config, message):
    if config.PUSHOVER_ENABLE == True:
        conn = httplib.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
            urllib.urlencode({
            "token": "qo0nwMNdX56KJl0Avd4NHE2onO4Xff",
            "user": config.PUSHOVER_USERTOKEN,
            "message": str(message),
            }), { "Content-type": "application/x-www-form-urlencoded" })

class AlarmServerConfig():
    def __init__(self, configfile):

        self._config = ConfigParser.ConfigParser()
        self._config.read(configfile)

        self.HTTPSPORT = self.read_config_var('alarmserver', 'httpsport', 8111, 'int')
        self.MAXEVENTS = self.read_config_var('alarmserver', 'maxevents', 10, 'int')
        self.MAXALLEVENTS = self.read_config_var('alarmserver', 'maxallevents', 100, 'int')
        self.ENVISALINKHOST = self.read_config_var('envisalink', 'host', 'envisalink', 'str')
        self.ENVISALINKPORT = self.read_config_var('envisalink', 'port', 4025, 'int')
        self.ENVISALINKPASS = self.read_config_var('envisalink', 'pass', 'user', 'str')
        self.ENABLEPROXY = self.read_config_var('envisalink', 'enableproxy', True, 'bool')
        self.ENVISALINKPROXYPORT = self.read_config_var('envisalink', 'proxyport', self.ENVISALINKPORT, 'int')
        self.ENVISALINKPROXYPASS = self.read_config_var('envisalink', 'proxypass', self.ENVISALINKPASS, 'str')
        self.PUSHOVER_ENABLE = self.read_config_var('pushover', 'enable', False, 'bool')
        self.PUSHOVER_USERTOKEN = self.read_config_var('pushover', 'enable', False, 'bool')
        self.ALARMCODE = self.read_config_var('envisalink', 'alarmcode', 1111, 'int')
        self.EVENTTIMEAGO = self.read_config_var('alarmserver', 'eventtimeago', True, 'bool')

        self.PARTITIONNAMES={}
        for i in range(1, MAXPARTITIONS+1):
            self.PARTITIONNAMES[i]=self.read_config_var('alarmserver', 'partition'+str(i), False, 'str', True)

        self.ZONENAMES={}
        for i in range(1, MAXZONES+1):
            self.ZONENAMES[i]=self.read_config_var('alarmserver', 'zone'+str(i), False, 'str', True)

        self.ALARMUSERNAMES={}
        for i in range(1, MAXALARMUSERS+1):
            self.ALARMUSERNAMES[i]=self.read_config_var('alarmserver', 'user'+str(i), False, 'str', True)

        if self.PUSHOVER_USERTOKEN == False and self.PUSHOVER_ENABLE == True: self.PUSHOVER_ENABLE = False

    def defaulting(self, section, variable, default, quiet = False):
        if quiet == False:
            alarmserver_logger('C:'+ str(variable) + ' not set in ['+str(section)+'] defaulting to: \''+str(default)+'\'')

    def read_config_var(self, section, variable, default, type = 'str', quiet = False):
        try:
            if type == 'str':
                return self._config.get(section,variable)
            elif type == 'bool':
                return self._config.getboolean(section,variable)
            elif type == 'int':
                return int(self._config.get(section,variable))
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            self.defaulting(section, variable, default, quiet)
            return default

class HTTPChannel(asynchat.async_chat):
    def __init__(self, server, sock, addr):
        asynchat.async_chat.__init__(self, sock)
        self.server = server
        self.set_terminator("\r\n\r\n")
        self.header = None
        self.data = ""
        self.shutdown = 0

    def collect_incoming_data(self, data):
        self.data = self.data + data
        if len(self.data) > 16384:
        # limit the header size to prevent attacks
            self.shutdown = 1

    def found_terminator(self):
        if not self.header:
            # parse http header
            fp = StringIO.StringIO(self.data)
            request = string.split(fp.readline(), None, 2)
            if len(request) != 3:
                # badly formed request; just shut down
                self.shutdown = 1
            else:
                # parse message header
                self.header = mimetools.Message(fp)
                self.set_terminator("\r\n")
                self.server.handle_request(
                    self, request[0], request[1], self.header
                    )
                self.close_when_done()
            self.data = ""
        else:
            pass # ignore body data, for now

    def pushstatus(self, status, explanation="OK"):
        self.push("HTTP/1.0 %d %s\r\n" % (status, explanation))

    def pushok(self, content):
        self.pushstatus(200, "OK")
        self.push('Content-type: text/html\r\n')
        self.push('Expires: Sat, 26 Jul 1997 05:00:00 GMT\r\n')
        self.push('Last-Modified: '+ datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")+' GMT\r\n')
        self.push('Cache-Control: no-store, no-cache, must-revalidate\r\n' ) 
        self.push('Cache-Control: post-check=0, pre-check=0\r\n') 
        self.push('Pragma: no-cache\r\n' )
        self.push('\r\n')
        self.push(content)

    def pushfile(self, file):
        self.pushstatus(200, "OK")
        extension = os.path.splitext(file)[1]
        if extension == ".html":
            self.push("Content-type: text/html\r\n")
        elif extension == ".js":
            self.push("Content-type: text/javascript\r\n")
        elif extension == ".png":
            self.push("Content-type: image/png\r\n")
        elif extension == ".css":
            self.push("Content-type: text/css\r\n")
        self.push("\r\n")
        self.push_with_producer(push_FileProducer('ext' + os.sep + file))

class EnvisalinkClient(asynchat.async_chat):
    def __init__(self, config):
        # Call parent class's __init__ method
        asynchat.async_chat.__init__(self)

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
            alarmserver_logger('Connection failed, retrying in '+str(self._retrydelay)+ ' seconds')
            for i in range(0, self._retrydelay):
                time.sleep(1)

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

        self.connect((self._config.ENVISALINKHOST, self._config.ENVISALINKPORT))

    def collect_incoming_data(self, data):
        # Append incoming data to the buffer
        self._buffer.append(data)

    def found_terminator(self):
        line = "".join(self._buffer)
        self.handle_line(line)
        self._buffer = []

    def handle_connect(self):
        alarmserver_logger("Connected to %s:%i" % (self._config.ENVISALINKHOST, self._config.ENVISALINKPORT))

    def handle_close(self):
        self._loggedin = False
        self.close()
        alarmserver_logger("Disconnected from %s:%i" % (self._config.ENVISALINKHOST, self._config.ENVISALINKPORT))
        self.do_connect(True)

    def handle_eerror(self):
        self._loggedin = False
        self.close()
        alarmserver_logger("Error, disconnected from %s:%i" % (self._config.ENVISALINKHOST, self._config.ENVISALINKPORT))
        self.do_connect(True)

    def send_command(self, code, data, checksum = True):
        if checksum == True:
            to_send = code+data+get_checksum(code,data)+'\r\n'
        else:
            to_send = code+data+'\r\n'

        alarmserver_logger('TX > '+to_send[:-1])
        self.push(to_send)

    def handle_line(self, input):
        if input != '':
            for client in CONNECTEDCLIENTS:
                CONNECTEDCLIENTS[client].send_command(input, False)

            code=int(input[:3])
            parameters=input[3:][:-2]
            event = getMessageType(int(code))
            message = self.format_event(event, parameters)
            alarmserver_logger('RX < ' +str(code)+' - '+message)

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
                        if self._config.PARTITIONNAMES[int(parameters[0])]!=False:
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
                                    if self._config.ALARMUSERNAMES[int(usercode)]!=False:
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
            alarmserver_logger('Incorrect envisalink password')
            sys.exit(0)

    def handle_event(self, code, parameters, event, message):
        if 'type' in event:
            if not event['type'] in ALARMSTATE: ALARMSTATE[event['type']]={'lastevents' : []}

            if event['type'] in ('partition', 'zone'):
                if event['type'] == 'zone':
                    if int(parameters) in self._config.ZONENAMES:
                        if not int(parameters) in ALARMSTATE[event['type']]: ALARMSTATE[event['type']][int(parameters)] = {'name' : self._config.ZONENAMES[int(parameters)]}
                    else:
                        if not int(parameters) in ALARMSTATE[event['type']]: ALARMSTATE[event['type']][int(parameters)] = {}
                elif event['type'] == 'partition':
                    if int(parameters) in self._config.PARTITIONNAMES:
                        if not int(parameters) in ALARMSTATE[event['type']]: ALARMSTATE[event['type']][int(parameters)] = {'name' : self._config.PARTITIONNAMES[int(parameters)]}
                    else:
                        if not int(parameters) in ALARMSTATE[event['type']]: ALARMSTATE[event['type']][int(parameters)] = {}
            else:
                if not int(parameters) in ALARMSTATE[event['type']]: ALARMSTATE[event['type']][int(parameters)] = {}

            if not 'lastevents' in ALARMSTATE[event['type']][int(parameters)]: ALARMSTATE[event['type']][int(parameters)]['lastevents'] = []
            if not 'status' in ALARMSTATE[event['type']][int(parameters)]:
                if not 'type' in event:
                    ALARMSTATE[event['type']][int(parameters)]['status'] = {}
                else:
                    ALARMSTATE[event['type']][int(parameters)]['status'] = evl_Defaults[event['type']]

            if 'status' in event:
                ALARMSTATE[event['type']][int(parameters)]['status']=dict_merge(ALARMSTATE[event['type']][int(parameters)]['status'], event['status'])

            if len(ALARMSTATE[event['type']][int(parameters)]['lastevents']) > self._config.MAXEVENTS:
                ALARMSTATE[event['type']][int(parameters)]['lastevents'].pop(0)
            ALARMSTATE[event['type']][int(parameters)]['lastevents'].append({'datetime' : str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), 'message' : message})

            if len(ALARMSTATE[event['type']]['lastevents']) > self._config.MAXALLEVENTS:
                ALARMSTATE[event['type']]['lastevents'].pop(0)
            ALARMSTATE[event['type']]['lastevents'].append({'datetime' : str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), 'message' : message})

    def handle_zone(self, code, parameters, event, message):
        self.handle_event(code, parameters[1:], event, message)

    def handle_partition(self, code, parameters, event, message):
        self.handle_event(code, parameters[0], event, message)

class push_FileProducer:
    # a producer which reads data from a file object

    def __init__(self, file):
        self.file = open(file, "rb")

    def more(self):
        if self.file:
            data = self.file.read(2048)
            if data:
                return data
            self.file = None
        return ""

class AlarmServer(asyncore.dispatcher):
    def __init__(self, config):
        # Call parent class's __init__ method
        asyncore.dispatcher.__init__(self)

        # Create Envisalink client object
        self._envisalinkclient = EnvisalinkClient(config)

        #Store config
        self._config = config

        # Create socket and listen on it
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(("", config.HTTPSPORT))
        self.listen(5)

    def handle_accept(self):
        # Accept the connection
        conn, addr = self.accept()
        alarmserver_logger('Incoming web connection from %s' % repr(addr))

        try:
            HTTPChannel(self, ssl.wrap_socket(conn, server_side=True, certfile="server.crt", keyfile="server.key", ssl_version=ssl.PROTOCOL_TLSv1), addr)
        except ssl.SSLError:
            alarmserver_logger('Failed https connection, attempted with http')
            return

    def handle_request(self, channel, method, request, header):
        alarmserver_logger('Web request: '+str(method)+' '+str(request))

        query = urlparse.urlparse(request)
        query_array = urlparse.parse_qs(query.query, True)

        if query.path == '/':
            channel.pushfile('index.html');
        elif query.path == '/api':
            channel.pushok(json.dumps(ALARMSTATE))
        elif query.path == '/api/alarm/arm':
            channel.pushok(json.dumps({'response' : 'Request to arm received'}))
            self._envisalinkclient.send_command('030', '1')
        elif query.path == '/api/alarm/stayarm':
            channel.pushok(json.dumps({'response' : 'Request to arm in stay received'}))
            self._envisalinkclient.send_command('031', '1')
        elif query.path == '/api/alarm/armwithcode':
            channel.pushok(json.dumps({'response' : 'Request to arm with code received'}))
            self._envisalinkclient.send_command('033', '1' + str(query_array['alarmcode'][0]))
        elif query.path == '/api/pgm':
            channel.pushok(json.dumps({'response' : 'Request to trigger PGM'}))
            #self._envisalinkclient.send_command('020', '1' + str(query_array['pgmnum'][0]))
            self._envisalinkclient.send_command('071', '1' + "*7" + str(query_array['pgmnum'][0]))
            time.sleep(1)
            self._envisalinkclient.send_command('071', '1' + str(query_array['alarmcode'][0]))
        elif query.path == '/api/alarm/disarm':
            channel.pushok(json.dumps({'response' : 'Request to disarm received'}))
            if 'alarmcode' in query_array:
                self._envisalinkclient.send_command('040', '1' + str(query_array['alarmcode'][0]))
            else:
                self._envisalinkclient.send_command('040', '1' + str(self._config.ALARMCODE))
        elif query.path == '/api/refresh':
            channel.pushok(json.dumps({'response' : 'Request to refresh data received'}))
            self._envisalinkclient.send_command('001', '')
        elif query.path == '/api/config/eventtimeago':
            channel.pushok(json.dumps({'eventtimeago' : str(self._config.EVENTTIMEAGO)}))
        elif query.path == '/img/glyphicons-halflings.png':
            channel.pushfile('glyphicons-halflings.png')
        elif query.path == '/img/glyphicons-halflings-white.png':
            channel.pushfile('glyphicons-halflings-white.png')
        elif query.path == '/favicon.ico':
            channel.pushfile('favicon.ico')
        else:
            if len(query.path.split('/')) == 2:
                try:
                    with open('ext' + os.sep + query.path.split('/')[1]) as f:
                        f.close()
                        channel.pushfile(query.path.split('/')[1])
                except IOError as e:
                    print "I/O error({0}): {1}".format(e.errno, e.strerror)
                    channel.pushstatus(404, "Not found")
                    channel.push("Content-type: text/html\r\n")
                    channel.push("File not found")
                    channel.push("\r\n")
            else:
                alarmserver_logger("Invalid file requested")
                channel.pushstatus(404, "Not found")
                channel.push("Content-type: text/html\r\n")
                channel.push("\r\n")

class ProxyChannel(asynchat.async_chat):
    def __init__(self, server, proxypass, sock, addr):
        asynchat.async_chat.__init__(self, sock)
        self.server = server
        self.set_terminator("\r\n")
        self._buffer = []
        self._server = server
        self._clientMD5 = hashlib.md5(str(addr)).hexdigest()
        self._straddr = str(addr)
        self._proxypass = proxypass
        self._authenticated = False

        self.send_command('5053')

    def collect_incoming_data(self, data):
        # Append incoming data to the buffer
        self._buffer.append(data)

    def found_terminator(self):
        line = "".join(self._buffer)
        self._buffer = []
        self.handle_line(line)

    def handle_line(self, line):
        alarmserver_logger('PROXY REQ < '+line)
        if self._authenticated == True:
            self._server._envisalinkclient.send_command(line, '', False)
        else:
            self.send_command('500005')
            expectedstring = '005' + self._proxypass + get_checksum('005', self._proxypass)
            if line == ('005' + self._proxypass + get_checksum('005', self._proxypass)):
                alarmserver_logger('Proxy User Authenticated')
                CONNECTEDCLIENTS[self._straddr]=self
                self._authenticated = True
                self.send_command('5051')
            else:
                alarmserver_logger('Proxy User Authentication failed')
                self.send_command('5050')
                self.close()

    def send_command(self, data, checksum = True):
        if checksum == True:
            to_send = data+get_checksum(data, '')+'\r\n'
        else:
            to_send = data+'\r\n'

        self.push(to_send)

    def handle_close(self):
        alarmserver_logger('Proxy connection from %s closed' % self._straddr)
        if self._straddr in CONNECTEDCLIENTS: del CONNECTEDCLIENTS[self._straddr]
        self.close()

    def handle_error(self):
        alarmserver_logger('Proxy connection from %s errored' % self._straddr)
        if self._straddr in CONNECTEDCLIENTS: del CONNECTEDCLIENTS[self._straddr]
        self.close()

class EnvisalinkProxy(asyncore.dispatcher):
    def __init__(self, config, server):
        self._config = config
        if self._config.ENABLEPROXY == False:
            return

        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        alarmserver_logger('Envisalink Proxy Started')

        self.bind(("", self._config.ENVISALINKPROXYPORT))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is None:
            pass
        else:
            sock, addr = pair
            alarmserver_logger('Incoming proxy connection from %s' % repr(addr))
            handler = ProxyChannel(server, self._config.ENVISALINKPROXYPASS, sock, addr)

if __name__=="__main__":
    alarmserver_logger('Alarm Server Starting')
    alarmserver_logger('Currently Supporting Envisalink 2DS/3 only')
    alarmserver_logger('Tested on a DSC-1616 + EVL-3')
    alarmserver_logger('and on a DSC-1832 + EVL-2DS')
    alarmserver_logger('Reading config file')

    config = AlarmServerConfig('alarmserver.cfg')

    server = AlarmServer(config)
    proxy = EnvisalinkProxy(config, server)

    try:
        while True:
            asyncore.loop(timeout=2, count=1)
            # insert scheduling code here.
    except KeyboardInterrupt:
        print "Crtl+C pressed. Shutting down."
