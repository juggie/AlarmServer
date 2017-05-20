import http.client, urllib.request, urllib.parse, urllib.error, json
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado import gen

from core import logger
from core.config import config
from core.events import events

ALARMSERVER_PUSHOVER_TOKEN = "qo0nwMNdX56KJl0Avd4NHE2onO4Xff"

def init():
    config.PUSHOVER_ENABLE = config.read_config_var('pushover', 'enable', False, 'bool')
    if config.PUSHOVER_ENABLE == True:
        config.PUSHOVER_USERTOKEN = config.read_config_var('pushover', 'usertoken', False, 'str')
        if config.PUSHOVER_USERTOKEN != False:
            config.PUSHOVER_IGNOREZONES = config.read_config_var('pushover', 'ignorezones', [], 'listint')
            config.PUSHOVER_IGNOREPARTITIONS = config.read_config_var('pushover', 'ignorepartitions', [], 'listint')
            logger.debug('Pushover Enabled - Partitions Ignored: %s - Zones Ignored: %s' 
                % (",".join([str (i) for i in config.PUSHOVER_IGNOREPARTITIONS]), ",".join([str(i) for i in config.PUSHOVER_IGNOREZONES])))
            events.register('statechange', sendNotification, config.PUSHOVER_IGNOREPARTITIONS, config.PUSHOVER_IGNOREZONES)

@gen.coroutine
def sendNotification(eventType, type, parameters, code, event, message, defaultStatus):
    http_client = AsyncHTTPClient()
    body = urllib.parse.urlencode({
        "token": ALARMSERVER_PUSHOVER_TOKEN,
        "user": config.PUSHOVER_USERTOKEN,
        "message": str(message)})
    res = yield http_client.fetch("https://api.pushover.net/1/messages.json", method='POST', headers={"Content-type": "application/x-www-form-urlencoded"}, body=body)
    logger.debug('Pushover notification sent')
