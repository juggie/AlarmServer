#!/usr/bin/python
## Alarm Server
## Supporting Envisalink 2DS/3
## Contributors: https://github.com/juggie/AlarmServer/graphs/contributors
## Compatibility: https://github.com/juggie/AlarmServer/wiki/Compatibility
##
## This code is under the terms of the GPL v3 license.

#python standard modules
import sys, getopt, os, glob

#alarm server modules
from core.config import config

#moved down to load have config has logger info loaded
#from core.state import state
#from core.events import events
#from core import logger
#from core import httpslistener
#from core import envisalink
#from core import envisalinkproxy

#TODO: move elsewhere
import tornado.ioloop

def main(argv):
    #welcome message
    #logger.info('Alarm Server Starting')

    #set default config
    conffile='alarmserver.cfg'

    try:
        opts, args = getopt.getopt(argv, "c:", ["config="])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-c", "--config"):
            conffile = arg

    #load config
    config.load(conffile)

    #now import since config file is loaded and logging can be ready
    from core.state import state
    from core.events import events
    from core import httpslistener
    from core import envisalink
    from core import envisalinkproxy

    #enable the state
    state.init()

    #set version
    state.setVersion(0.3)

    #start envisalink client
    alarmclient = envisalink.Client()

    #start envisalink proxy
    alarmproxy = envisalinkproxy.Proxy()

    #start https server
    if config.HTTPS == True:
        httpsserver = httpslistener.start()

    #start http server
    if config.HTTP == True:
        httpserver = httpslistener.start(https = False)

    #load plugins - TODO: make this way better
    currpath = os.path.dirname(os.path.abspath(__file__))
    plugins = glob.glob(currpath+"/plugins/*.py")
    for p in plugins:
        if str.find(p, '__init__.py') != -1: continue
        name = p[p.rfind('/')+1:p.find('.')]
        exec "from plugins import %s" % name
        exec "%s.init()" % name

    #start tornado ioloop
    tornado.ioloop.IOLoop.instance().start()

if __name__=="__main__":
    main(sys.argv[1:])
