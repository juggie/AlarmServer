import logger

class events():
    @staticmethod
    def register(eventType, callback):
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
        
        events.listeners[eventType].append(callback)
        logger.debug('Registered Callback for: %s' % eventType)

    @staticmethod
    def put(eventType, payload):
        for c in events.listeners[eventType]:
            c(eventType, **payload)
