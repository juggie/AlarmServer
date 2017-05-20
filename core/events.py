from . import logger

class events():
    @staticmethod
    def register(eventType, callback, partitionFilter = [], zoneFilter = []):
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

        events.listeners[eventType].append({'callback' : callback, 'partitionFilter' : partitionFilter, 'zoneFilter' : zoneFilter})
        logger.debug('Registered Callback for: %s' % eventType)

    @staticmethod
    def put(eventType, type = None, parameters = None, *args):
        try:
            for c in events.listeners[eventType]:
                if ((type == 'partition' and parameters not in c['partitionFilter']) 
                        or (type == 'zone' and parameters not in c['zoneFilter']) 
                        or (type not in ['partition', 'zone'])):
                    c['callback'](eventType, type, parameters, *args)
                else:
                    logger.debug('Event type: %s/%s parameters: %s Filtered' % (eventType, type, parameters))
        except KeyError:
            logger.debug('No handler registered for: %s' % eventType)
