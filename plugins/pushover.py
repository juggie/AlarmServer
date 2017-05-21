"""Pushover module"""
import urllib.request
import urllib.parse
import urllib.error
from tornado.httpclient import AsyncHTTPClient
from tornado import gen

from core import logger
from core.events import events

ALARMSERVER_PUSHOVER_TOKEN = "qo0nwMNdX56KJl0Avd4NHE2onO4Xff"

def init(config):
    """Init function for pushover plugin"""
    config.PUSHOVER_ENABLE = config.get_val('pushover', 'enable', False, 'bool')
    if config.PUSHOVER_ENABLE:
        config.PUSHOVER_USERTOKEN = config.get_val('pushover', 'usertoken', False, 'str')
        if config.PUSHOVER_USERTOKEN != False:
            config.PUSHOVER_IGNOREZONES = \
                config.get_val('pushover', 'ignorezones', [], 'listint')
            config.PUSHOVER_IGNOREPARTITIONS = \
                config.get_val('pushover', 'ignorepartitions', [], 'listint')
            logger.debug('Pushover Enabled - Partitions Ignored: %s - Zones Ignored: %s' \
                % (",".join([str(i) for i in config.PUSHOVER_IGNOREPARTITIONS]), \
                ",".join([str(i) for i in config.PUSHOVER_IGNOREZONES])))
            events.register('statechange', send_notification, config.PUSHOVER_IGNOREPARTITIONS, \
                config.PUSHOVER_IGNOREZONES)

@gen.coroutine
def send_notification(config, eventType, type, parameters, code, event, message, defaultStatus):
    """Send pushover notificiation"""
    http_client = AsyncHTTPClient()
    body = urllib.parse.urlencode({
        "token": ALARMSERVER_PUSHOVER_TOKEN,
        "user": config.PUSHOVER_USERTOKEN,
        "message": str(message)})
    yield http_client.fetch("https://api.pushover.net/1/messages.json", \
        method='POST', headers={"Content-type": "application/x-www-form-urlencoded"}, body=body)
    logger.debug('Pushover notification sent')
