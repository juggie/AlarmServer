import httplib, urllib, sys, json
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado import gen

from core import logger
from core.config import config
from core.events import events

def init():
    config.PUSHOVER_ENABLE = config.read_config_var('pushover', 'enable', False, 'bool')
    if config.PUSHOVER_ENABLE == True:
        config.PUSHOVER_USERTOKEN = config.read_config_var('pushover', 'usertoken', False, 'str')
        if config.PUSHOVER_USERTOKEN != False:
            logger.debug('Pushover Enabled')
            events.register('statechange', sendNotification)

@gen.coroutine
def sendNotification(eventType, type, code, parameters, event, message, defaultStatus):
    if config.PUSHOVER_ENABLE == True:
        http_client = AsyncHTTPClient()
        body = urllib.urlencode({
            "token": "qo0nwMNdX56KJl0Avd4NHE2onO4Xff",
            "user": config.PUSHOVER_USERTOKEN,
            "message": str(message)})
        res = yield http_client.fetch("https://api.pushover.net/1/messages.json", method='POST', headers={"Content-type": "application/x-www-form-urlencoded"}, body=body)
