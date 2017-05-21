#!/usr/bin/python

"""Alarm Server
Supporting Envisalink 2DS/3/4
Contributors: https://github.com/juggie/AlarmServer/graphs/contributors
Compatibility: https://github.com/juggie/AlarmServer/wiki/Compatibility
This code is under the terms of the GPL v3 license."""

#python standard modules
import sys
import getopt
import os
import glob
import importlib

#alarm server modules
from core.config import Config
from core.state import State
from core import logger
from core import httpslistener
from core import envisalink
from core import envisalinkproxy

import tornado.ioloop

def main(argv):
    """Alarmserver entrypoint"""
    logger.info('Alarm Server Starting')

    try:
        #pylint: disable=W0612
        opts, args = getopt.getopt(argv, "c:", ["config="])
        #pylint: enable=W0612
    except getopt.GetoptError:
        sys.exit(2)

    if opts:
        for opt, arg in opts:
            if opt in ("-c", "--config"):
                config = Config(arg)
    else:
        config = Config()

    #start logger
    if config.logfile:
        logger.start(config.logfile)
    else:
        logger.start()

    #enable the state
    State.init(config)

    #set version
    State.set_version(0.3)

    #pylint: disable=W0612
    #start envisalink client
    alarmclient = envisalink.Client(config)

    #start envisalink proxy
    alarmproxy = envisalinkproxy.Proxy(config)

    #start https server
    if config.https:
        httpsserver = httpslistener.start(config)

    #start http server
    if config.http:
        httpserver = httpslistener.start(config, https=False)
    #pylint: enable=W0612

    #load plugins - TODO: make this way better
    currpath = os.path.dirname(os.path.abspath(__file__))
    plugins = glob.glob(currpath+"/plugins/*.py")
    for plug in plugins:
        if str.find(plug, '__init__.py') != -1:
            continue
        base = os.path.basename(plug)
        name = os.path.splitext(base)[0]
        getattr(importlib.import_module("plugins.{}".format(name)), 'init')(config)

    #start tornado ioloop
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main(sys.argv[1:])
