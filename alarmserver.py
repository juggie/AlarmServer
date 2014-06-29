#!/usr/bin/python
## Alarm Server
## Supporting Envisalink 2DS/3
## Written by donnyk+envisalink@gmail.com
## Lightly improved by leaberry@gmail.com
##
## This code is under the terms of the GPL v3 license.


import asyncore, asynchat
import ConfigParser
import datetime
import os, socket, string, sys, httplib, urllib, urlparse, ssl
import json
import hashlib
import time
import getopt
import logging

logger = logging.getLogger('alarmserver')
logger.setLevel(logging.DEBUG)

# console handler
ch = logging.StreamHandler();
ch.setLevel(logging.ERROR)
# file handler
fh = logging.FileHandler('output.log', mode='w');
fh.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter);
fh.setFormatter(formatter)
# add handlers to logger
logger.addHandler(ch)
logger.addHandler(fh)

import HTTPChannel
import Envisalink

LOGTOFILE = False

class CodeError(Exception): pass

MAXPARTITIONS=16
MAXZONES=128
MAXALARMUSERS=47
CONNECTEDCLIENTS={}

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

        self.LOGURLREQUESTS = self.read_config_var('alarmserver', 'logurlrequests', True, 'bool')
        self.HTTPSPORT = self.read_config_var('alarmserver', 'httpsport', 8111, 'int')
        self.CERTFILE = self.read_config_var('alarmserver', 'certfile', 'server.crt', 'str')
        self.KEYFILE = self.read_config_var('alarmserver', 'keyfile', 'server.key', 'str')
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
        self.LOGFILE = self.read_config_var('alarmserver', 'logfile', '', 'str')
        global LOGTOFILE
        if self.LOGFILE == '':
            LOGTOFILE = False
        else:
            LOGTOFILE = True

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
            print('Config option '+ str(variable) + ' not set in ['+str(section)+'] defaulting to: \''+str(default)+'\'')

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

class AlarmServer(asyncore.dispatcher):
    def __init__(self, config):
        # Call parent class's __init__ method
        asyncore.dispatcher.__init__(self)

        # Create Envisalink client object
        self._envisalinkclient = Envisalink.Client(config, CONNECTEDCLIENTS)

        #Store config
        self._config = config

        logger.info('AlarmServer on HTTPS port {}'.format(config.HTTPSPORT))

        # Create socket and listen on it
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind(("", config.HTTPSPORT))
        self.listen(5)

    def handle_accept(self):
        # Accept the connection
        conn, addr = self.accept()
        if (config.LOGURLREQUESTS):
            logger.info('Incoming web connection from %s' % repr(addr))

        try:
            HTTPChannel.HTTPChannel(self, ssl.wrap_socket(conn, server_side=True, certfile=config.CERTFILE, keyfile=config.KEYFILE, ssl_version=ssl.PROTOCOL_TLSv1), addr)
        except ssl.SSLError:
            logger.warning('Failed https connection, attempted with http')
            return

    def handle_request(self, channel, method, request, header):
        if (config.LOGURLREQUESTS):
            logger.info('Web request: '+str(method)+' '+str(request))

        query = urlparse.urlparse(request)
        query_array = urlparse.parse_qs(query.query, True)

        if query.path == '/':
            channel.pushfile('index.html');
        elif query.path == '/api':
            channel.pushok(json.dumps(self._envisalinkclient._alarmstate))
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
                    with open(sys.path[0] + os.sep + 'ext' + os.sep + query.path.split('/')[1]) as f:
                        f.close()
                        channel.pushfile(query.path.split('/')[1])
                except IOError as e:
                    print "I/O error({0}): {1}".format(e.errno, e.strerror)
                    channel.pushstatus(404, "Not found")
                    channel.push("Content-type: text/html\r\n")
                    channel.push("File not found")
                    channel.push("\r\n")
            else:
                if (config.LOGURLREQUESTS):
                    logger.info("Invalid file requested")

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
        logger.info('PROXY REQ < '+line)
        if self._authenticated == True:
            self._server._envisalinkclient.send_command(line, '', False)
        else:
            self.send_command('500005')
            expectedstring = '005' + self._proxypass + get_checksum('005', self._proxypass)
            if line == ('005' + self._proxypass + get_checksum('005', self._proxypass)):
                logger.info('Proxy User Authenticated')
                CONNECTEDCLIENTS[self._straddr]=self
                self._authenticated = True
                self.send_command('5051')
            else:
                logger.info('Proxy User Authentication failed')
                self.send_command('5050')
                self.close()

    def send_command(self, data, checksum = True):
        if checksum == True:
            to_send = data+get_checksum(data, '')+'\r\n'
        else:
            to_send = data+'\r\n'

        self.push(to_send)

    def handle_close(self):
        logger.info('Proxy connection from %s closed' % self._straddr)
        if self._straddr in CONNECTEDCLIENTS: del CONNECTEDCLIENTS[self._straddr]
        self.close()

    def handle_error(self):
        logger.error('Proxy connection from %s errored' % self._straddr)
        if self._straddr in CONNECTEDCLIENTS: del CONNECTEDCLIENTS[self._straddr]
        self.close()

def usage():
    print 'Usage: '+sys.argv[0]+' -c <configfile>'

def main(argv):
    try:
      opts, args = getopt.getopt(argv, "hc:", ["help", "config="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-c", "--config"):
            global conffile
            conffile = arg


if __name__=="__main__":
    conffile='alarmserver.cfg'
    main(sys.argv[1:])
    logger.info('Using configuration file %s' % conffile)
    config = AlarmServerConfig(conffile)
    #if LOGTOFILE:
    #    outfile=open(config.LOGFILE,'a')

    logger.info('-'*30)
    logger.info('Alarm Server Starting')
    logger.debug('Currently Supporting Envisalink 2DS/3 only')
    logger.debug('Tested on a DSC-1616 + EVL-3')
    logger.debug('and on a DSC-1832 + EVL-2DS')
    logger.debug('and on a DSC-1864 v4.6 + EVL-3')

    server = AlarmServer(config)
    proxy = Envisalink.Proxy(config, server)

    try:
        while True:
            asyncore.loop(timeout=2, count=1)
            # insert scheduling code here.
    except KeyboardInterrupt:
        print "Crtl+C pressed. Shutting down."
        logger.info('Shutting down from Ctrl+C')
        #if LOGTOFILE:
        #    outfile.close()

        server.shutdown(socket.SHUT_RDWR)
        server.close()
        sys.exit()
