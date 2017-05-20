"""IFTTT Maker plugin"""
import urllib.request
import urllib.parse
import urllib.error
import json
from tornado.httpclient import AsyncHTTPClient
from tornado import gen

from core import logger
from core.config import Config
from core.events import events

def init():
    """Init function for pushbullet plugin"""
    Config.PUSHBULLET_ENABLE = \
        Config.read_config_var('pushbullet', 'enable', False, 'bool')
    if Config.PUSHBULLET_ENABLE:
        Config.PUSHBULLET_USERTOKEN = \
            Config.read_config_var('pushbullet', 'usertoken', False, 'str')
        if Config.PUSHBULLET_USERTOKEN != False:
            Config.PUSHBULLET_IGNOREZONES = \
                Config.read_config_var('pushbullet', 'ignorezones', [], 'listint')
            Config.PUSHBULLET_IGNOREPARTITIONS = \
                Config.read_config_var('pushbullet', 'ignorepartitions', [], 'listint')
            logger.debug('PUSHBULLET Enabled - Partitions Ignored: %s - Zones Ignored: %s' \
                % (",".join([str(i) for i in Config.PUSHBULLET_IGNOREPARTITIONS]), \
                ",".join([str(i) for i in Config.PUSHBULLET_IGNOREZONES])))
            events.register('statechange', send_notification, \
                Config.PUSHBULLET_IGNOREPARTITIONS, Config.PUSHBULLET_IGNOREZONES)
            pushbulletRequest('login')

def send_notification(eventType, type, parameters, code, event, message, defaultStatus):
    """Send pushbullet notification"""
    pushbulletRequest('notify', message)

@gen.coroutine
def pushbulletRequest(type, message=None):
    """Make an pushbullet request"""
    http_client = AsyncHTTPClient()
    if type == 'login':
        res = yield http_client.fetch("https://api.pushbullet.com/v2/users/me", method='GET', \
            headers={"Access-Token": Config.PUSHBULLET_USERTOKEN})
        userdetails = json.loads(res.body)
        #todo add code to handle login error and disable plugin
        logger.debug('Pushover enabled - User: %(name)s Email: %(email)s' % userdetails)
    elif type == 'notify':
        body = urllib.parse.urlencode({"body": message, "title":"AlarmServer", "type":"note"})
        res = yield http_client.fetch("https://api.pushbullet.com/v2/pushes", method='POST', \
            headers={"Access-Token": Config.PUSHBULLET_USERTOKEN}, body=body)
    else:
        logger.error('Unsupported pushbullet request')
