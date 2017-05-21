"""IFTTT Maker plugin"""
import urllib.request
import urllib.parse
import urllib.error
import json
from tornado.httpclient import AsyncHTTPClient
from tornado import gen

from core import logger
from core.events import events

def init(config):
    """Init function for pushbullet plugin"""
    config.PUSHBULLET_ENABLE = \
        config.get_val('pushbullet', 'enable', False, 'bool')
    if config.PUSHBULLET_ENABLE:
        config.PUSHBULLET_USERTOKEN = \
            config.get_val('pushbullet', 'usertoken', False, 'str')
        if config.PUSHBULLET_USERTOKEN != False:
            config.PUSHBULLET_IGNOREZONES = \
                config.get_val('pushbullet', 'ignorezones', [], 'listint')
            config.PUSHBULLET_IGNOREPARTITIONS = \
                config.get_val('pushbullet', 'ignorepartitions', [], 'listint')
            logger.debug('PUSHBULLET Enabled - Partitions Ignored: %s - Zones Ignored: %s' \
                % (",".join([str(i) for i in config.PUSHBULLET_IGNOREPARTITIONS]), \
                ",".join([str(i) for i in config.PUSHBULLET_IGNOREZONES])))
            events.register('statechange', send_notification, \
                config.PUSHBULLET_IGNOREPARTITIONS, config.PUSHBULLET_IGNOREZONES)
            pushbulletRequest('login')

def send_notification(config, eventType, type, parameters, code, event, message, defaultStatus):
    """Send pushbullet notification"""
    pushbulletRequest('notify', message)

@gen.coroutine
def pushbulletRequest(type, message=None):
    """Make an pushbullet request"""
    http_client = AsyncHTTPClient()
    if type == 'login':
        res = yield http_client.fetch("https://api.pushbullet.com/v2/users/me", method='GET', \
            headers={"Access-Token": config.PUSHBULLET_USERTOKEN})
        userdetails = json.loads(res.body)
        #todo add code to handle login error and disable plugin
        logger.debug('Pushover enabled - User: %(name)s Email: %(email)s' % userdetails)
    elif type == 'notify':
        body = urllib.parse.urlencode({"body": message, "title":"AlarmServer", "type":"note"})
        res = yield http_client.fetch("https://api.pushbullet.com/v2/pushes", method='POST', \
            headers={"Access-Token": config.PUSHBULLET_USERTOKEN}, body=body)
    else:
        logger.error('Unsupported pushbullet request')
