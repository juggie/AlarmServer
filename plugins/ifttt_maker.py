import http.client, urllib.request, urllib.parse, urllib.error, json
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado import gen

from core import logger
from core.config import config
from core.events import events

def init():
    ifttt_maker_config_session_name = 'ifttt_maker'

    config.IFTTT_MAKER_ENABLE = config.read_config_var(ifttt_maker_config_session_name, 'enable', False, 'bool') #todo fix me
    if config.IFTTT_MAKER_ENABLE == True:
        config.IFTTT_MAKER_KEY = config.read_config_var(ifttt_maker_config_session_name, 'key', False, 'str')
        config.IFTTT_MAKER_EVENT_NAME = config.read_config_var(ifttt_maker_config_session_name, 'eventName', False, 'str')
        if config.IFTTT_MAKER_KEY != False:
            config.IFTTT_MAKER_IGNOREZONES = config.read_config_var(ifttt_maker_config_session_name, 'ignorezones', [], 'listint')
            config.IFTTT_MAKER_IGNOREPARTITIONS = config.read_config_var(ifttt_maker_config_session_name, 'ignorepartitions', [], 'listint')
            logger.debug('IFTTT_MAKER Enabled - Partitions Ignored: %s - Zones Ignored: %s'
                % (",".join([str (i) for i in config.IFTTT_MAKER_IGNOREPARTITIONS]), ",".join([str(i) for i in config.IFTTT_MAKER_IGNOREZONES])))
            events.register('statechange', sendNotification, config.IFTTT_MAKER_IGNOREPARTITIONS, config.IFTTT_MAKER_IGNOREZONES)
 
def sendNotification(eventType, type, parameters, code, event, message, defaultStatus):
        iftttMakerRequest('notify', message)

@gen.coroutine
def iftttMakerRequest(eventType, message = None):
    http_client = AsyncHTTPClient()
    if iftttMakerRequestType == 'notify':
        # Build event Json body
        body = urllib.parse.urlencode({'value1': message})
        url = 'https://maker.ifttt.com/trigger/' + config.IFTTT_MAKER_EVENT_NAME + '/with/key/' + config.IFTTT_MAKER_KEY

        logger.debug('IFTTT_MAKER: Pushing event: ' + url + ' with body: ' + body)
        res = yield http_client.fetch(url, method='POST', body=body)

        # Check result
        if res.code == 200:
              logger.debug('IFTTT_MAKER: Event pushed successfully')
        else:
              logger.debug('IFTTT_MAKER: Error pushing event: ' + str(res))
    else:
        logger.error('Unsupported ifttt_maker request')
