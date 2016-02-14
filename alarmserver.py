#!/usr/bin/python
## Alarm Server
## Supporting Envisalink 2DS/3
## Contributors: https://github.com/juggie/AlarmServer/graphs/contributors
## Compatibility: https://github.com/juggie/AlarmServer/wiki/Compatibility
##
## This code is under the terms of the GPL v3 license.

#python standard modules
import sys, getopt, os

#alarm server modules
from alarmserver import logger
from alarmserver.config import config
import alarmserver.httpslistener
import alarmserver.envisalink

#TODO: move elsewhere
import tornado.ioloop

def main(argv):
    #welcome message
    logger.info('Alarm Server Starting')

    #set default config
    conffile='alarmserver.cfg'

    #load config
    config.load(conffile)    

    #start envisalink client
    alarmclient = alarmserver.envisalink.Client()

    #start http server
    httpsserver = alarmserver.httpslistener.start(alarmclient)

    #start tornado ioloop
    tornado.ioloop.IOLoop.instance().start()

if __name__=="__main__":
    main(sys.argv[1:])
