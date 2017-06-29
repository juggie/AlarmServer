import httplib, urllib, json
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado import gen

from core import logger
from core.config import config
from core.events import events

def init():
    config.SMARTTHINGS_ENABLE = config.read_config_var('smartthings', 'enable', False, 'bool')
    if config.SMARTTHINGS_ENABLE == True:
        config.SMARTTHINGS_ACCESS_TOKEN = config.read_config_var('smartthings', 'access_token', False, 'str')
        config.SMARTTHINGS_URL_BASE = config.read_config_var('smartthings', 'url_base', False, 'str')
        config.SMARTTHINGS_APP_ID = config.read_config_var('smartthings', 'app_id', False, 'str')
        config.SMARTTHINGS_EVENT_CODES = config.read_config_var('smartthings', 'event_codes', [], 'listint')
        logger.debug('SMARTTHINGS Enabled - event codes: %s' % (",".join([str (i) for i in config.SMARTTHINGS_EVENT_CODES])))
        events.register('statechange', sendStNotification, [], [])
        events.register('stateinit', sendStNotification, [], [])

def sendStNotification(eventType, type, parameters, code, event, message, defaultStatus):
    # logger.debug('sendStNotification')
    # logger.debug('eventType %s' % eventType)
    # logger.debug('type %s' % type)
    # logger.debug('parameters %s' % parameters)
    # logger.debug('code %d' % code)
    # logger.debug('event %s' % event)
    # logger.debug('message %s' % message)
    # logger.debug('defaultStatus %s' % defaultStatus)
    smartthingsRequest(eventType, type, parameters, code, event, message, defaultStatus)

@gen.coroutine
def smartthingsRequest(eventType, type, parameters, code, event, message, defaultStatus):
    http_client = AsyncHTTPClient()
    url = 'garbage'
    if type == 'zone':
        url = config.SMARTTHINGS_URL_BASE + "/" + config.SMARTTHINGS_APP_ID + "/panel/" + str(code) + "/" + str(int(parameters)) + "?access_token=" + config.SMARTTHINGS_ACCESS_TOKEN
    elif type == 'partition':
        url = config.SMARTTHINGS_URL_BASE + "/" + config.SMARTTHINGS_APP_ID + "/panel/" + str(code) + "/" + str(int(parameters[0])) + "?access_token=" + config.SMARTTHINGS_ACCESS_TOKEN
    else:
        logger.debug('Smartthings unhandled type: ' + type)
        return
    # logger.debug('Smartthings will send %s request: %s' % (type, url))
    try:
        res = yield http_client.fetch(url, method='GET')
    except:
        logger.debug('Smartthings exception for url %s' % url)
    # logger.debug('Smartthings result: %s' % res)
