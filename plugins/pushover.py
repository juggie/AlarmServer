import httplib, urllib, sys, json
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado import gen

from core import logger
from core.config import config
from core.events import events

def init():
    events.register('statechange', sendNotification)

@gen.coroutine
def sendNotification(type, eventType, code, parameters, event, message, defaultStatus):
    if config.PUSHOVER_ENABLE == True:
        http_client = AsyncHTTPClient()
        body = urllib.urlencode({
            "token": "qo0nwMNdX56KJl0Avd4NHE2onO4Xff",
            "user": config.PUSHOVER_USERTOKEN,
            "message": str(message)})
        res = yield http_client.fetch("https://api.pushover.net/1/messages.json", method='POST', headers={"Content-type": "application/x-www-form-urlencoded"}, body=body)
