"""Pushover module"""
import urllib.request
import urllib.parse
import urllib.error
from tornado.httpclient import AsyncHTTPClient
from tornado import gen

from core import logger
from core.config import Config
from core.events import events

ALARMSERVER_PUSHOVER_TOKEN = "qo0nwMNdX56KJl0Avd4NHE2onO4Xff"

def init():
    """Init function for pushover plugin"""
    Config.PUSHOVER_ENABLE = Config.read_config_var('pushover', 'enable', False, 'bool')
    if Config.PUSHOVER_ENABLE:
        Config.PUSHOVER_USERTOKEN = Config.read_config_var('pushover', 'usertoken', False, 'str')
        if Config.PUSHOVER_USERTOKEN != False:
            Config.PUSHOVER_IGNOREZONES = \
                Config.read_config_var('pushover', 'ignorezones', [], 'listint')
            Config.PUSHOVER_IGNOREPARTITIONS = \
                Config.read_config_var('pushover', 'ignorepartitions', [], 'listint')
            logger.debug('Pushover Enabled - Partitions Ignored: %s - Zones Ignored: %s' \
                % (",".join([str(i) for i in Config.PUSHOVER_IGNOREPARTITIONS]), \
                ",".join([str(i) for i in Config.PUSHOVER_IGNOREZONES])))
            events.register('statechange', send_notification, Config.PUSHOVER_IGNOREPARTITIONS, \
                Config.PUSHOVER_IGNOREZONES)

@gen.coroutine
def send_notification(eventType, type, parameters, code, event, message, defaultStatus):
    """Send pushover notificiation"""
    http_client = AsyncHTTPClient()
    body = urllib.parse.urlencode({
        "token": ALARMSERVER_PUSHOVER_TOKEN,
        "user": Config.PUSHOVER_USERTOKEN,
        "message": str(message)})
    yield http_client.fetch("https://api.pushover.net/1/messages.json", \
        method='POST', headers={"Content-type": "application/x-www-form-urlencoded"}, body=body)
    logger.debug('Pushover notification sent')
