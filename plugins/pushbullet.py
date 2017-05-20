import http.client, urllib.request, urllib.parse, urllib.error, json
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado import gen

from core import logger
from core.config import config
from core.events import events

def init():
    config.PUSHBULLET_ENABLE = config.read_config_var('pushbullet', 'enable', False, 'bool') #todo fix me
    if config.PUSHBULLET_ENABLE == True:
        config.PUSHBULLET_USERTOKEN = config.read_config_var('pushbullet', 'usertoken', False, 'str')
        if config.PUSHBULLET_USERTOKEN != False:
            config.PUSHBULLET_IGNOREZONES = config.read_config_var('pushbullet', 'ignorezones', [], 'listint')
            config.PUSHBULLET_IGNOREPARTITIONS = config.read_config_var('pushbullet', 'ignorepartitions', [], 'listint')
            logger.debug('PUSHBULLET Enabled - Partitions Ignored: %s - Zones Ignored: %s' 
                % (",".join([str (i) for i in config.PUSHBULLET_IGNOREPARTITIONS]), ",".join([str(i) for i in config.PUSHBULLET_IGNOREZONES])))
            events.register('statechange', sendNotification, config.PUSHBULLET_IGNOREPARTITIONS, config.PUSHBULLET_IGNOREZONES)
            pushbulletRequest('login')

def sendNotification(eventType, type, parameters, code, event, message, defaultStatus):
	pushbulletRequest('notify', message)

@gen.coroutine
def pushbulletRequest(type, message = None):
    http_client = AsyncHTTPClient()
    if type == 'login':
        res = yield http_client.fetch("https://api.pushbullet.com/v2/users/me", method='GET', headers={"Access-Token": config.PUSHBULLET_USERTOKEN})
        userdetails = json.loads(res.body)
        #todo add code to handle login error and disable plugin
        logger.debug('Pushover enabled - User: %(name)s Email: %(email)s' % userdetails)
    elif type == 'notify':
        body = urllib.parse.urlencode({"body": message,"title":"AlarmServer","type":"note"})
        res = yield http_client.fetch("https://api.pushbullet.com/v2/pushes", method='POST', headers={"Access-Token": config.PUSHBULLET_USERTOKEN}, body=body)
    else:
        logger.error('Unsupported pushbullet request')
