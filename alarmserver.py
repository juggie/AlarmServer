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
from core.config import config
from core.state import state
from core import logger
from core import httpslistener
from core import envisalink

#TODO: move elsewhere
import tornado.ioloop

def main(argv):
    #welcome message
    logger.info('Alarm Server Starting')

    #set default config
    conffile='alarmserver.cfg'

    #load config
    config.load(conffile)

    #enable the state
    state.init()

    #set version
    state.setVersion(0.3)

    #start envisalink client
    alarmclient = envisalink.Client()

    #start https server
    httpsserver = httpslistener.start(alarmclient)

    #start http server TODO: add code to disable/enable in config
    httpserver = httpslistener.start(alarmclient, https = False)

    #start tornado ioloop
    tornado.ioloop.IOLoop.instance().start()

if __name__=="__main__":
    main(sys.argv[1:])
