"""Pushover module"""
try:
    from urllib.request import urlopen
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
    from urllib import urlopen

from tornado.httpclient import AsyncHTTPClient
from tornado import gen

from core import logger
from core.events import Events

class pushover(object):
    """Pushover plugin class"""
    def __init__(self, config):
        """Init function for pushover plugin"""
        self.config = config
        self.pushover_token = "qo0nwMNdX56KJl0Avd4NHE2onO4Xff"
        config.PUSHOVER_ENABLE = config.get_val('pushover', 'enable', False, 'bool')
        if config.PUSHOVER_ENABLE:
            config.PUSHOVER_USERTOKEN = config.get_val('pushover', 'usertoken', False, 'str')
            if config.PUSHOVER_USERTOKEN != False:
                config.PUSHOVER_IGNOREZONES = config.get_val('pushover',
                                                             'ignorezones', [], 'listint')
                config.PUSHOVER_IGNOREPARTITIONS = config.get_val('pushover',
                                                                  'ignorepartitions', [], 'listint')
                logger.debug('Pushover Enabled - Partitions Ignored: %s - Zones Ignored: %s'
                             % (",".join([str(i) for i in config.PUSHOVER_IGNOREPARTITIONS]),
                                ",".join([str(i) for i in config.PUSHOVER_IGNOREZONES])))
                Events.register('statechange', self.send_notification,
                                config.PUSHOVER_IGNOREPARTITIONS, config.PUSHOVER_IGNOREZONES)

    @gen.coroutine
    def send_notification(self, event_type, type, parameters, code, event, message, default_status):
        """Send pushover notificiation"""
        http_client = AsyncHTTPClient()
        body = urllib.parse.urlencode({
            "token": self.pushover_token,
            "user": self.config.PUSHOVER_USERTOKEN,
            "message": str(message)})
        yield http_client.fetch("https://api.pushover.net/1/messages.json",
                                method='POST',
                                headers={"Content-type": "application/x-www-form-urlencoded"},
                                body=body)
        logger.debug('Pushover notification sent')
