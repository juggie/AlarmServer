import logger
import sys

class events():
    @staticmethod
    def register(eventType, callback, filter = None):
        #check to see if our dict exists
        try:
            events.listeners
        except AttributeError:
            events.listeners = {}

        #check to see if our set exists
        try:
            events.listeners[eventType]
        except KeyError:
            events.listeners[eventType] = []

        events.listeners[eventType].append({'callback' : callback, 'filter' : filter})
        logger.debug('Registered Callback for: %s' % eventType)

    @staticmethod
    def put(eventType, type = None, parameters = None, *args):
        try:
            for c in events.listeners[eventType]:
                #TODO: write code to implement filter
                c['callback'](eventType, type, parameters, *args)
        except KeyError:
            logger.debug('No handler registered for: %s' % eventType)
