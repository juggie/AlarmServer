"""Alarmserver events"""
#pylint: disable=W0102
from . import logger

class Events():
    """Events class"""
    @staticmethod
    def register(event_type, callback, partition_filter=[], zone_filter=[]):
        """Register event"""
        #check to see if our dict exists
        try:
            Events.listeners
        except AttributeError:
            Events.listeners = {}

        #check to see if our set exists
        try:
            Events.listeners[event_type]
        except KeyError:
            Events.listeners[event_type] = []

        Events.listeners[event_type].append({'callback' : callback,
                                             'partition_filter' : partition_filter,
                                             'zone_filter' : zone_filter})
        logger.debug('Registered Callback for: %s' % event_type)

    @staticmethod
    def put(event_type, type=None, parameters=None, *args):
        """Put an event"""
        try:
            for connection in Events.listeners[event_type]:
                if ((type == 'partition' and parameters not in connection['partition_filter'])
                        or (type == 'zone' and parameters not in connection['zone_filter'])
                        or (type not in ['partition', 'zone'])):
                    connection['callback'](event_type, type, parameters, *args)
                else:
                    logger.debug('Event type: %s/%s parameters: %s Filtered' %
                                 (event_type, type, parameters))
        except KeyError:
            logger.debug('No handler registered for: %s' % event_type)
