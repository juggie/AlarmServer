import datetime

#alarmserver modules
import logger
from config import config
from events import events

class state():
    logger.debug('State Module Loaded')

    @staticmethod
    def init():
        state.state = {}
        events.register('alarm', state.update)

    @staticmethod
    def getDict():
        return state.state

    @staticmethod
    def setVersion(version):
        state.state['version'] = version

    @staticmethod
    def update(eventType, type, parameters, code, event, message, defaultStatus):
        if not type in state.state: state.state[type] = {'lastevents' : []}

        #keep the last state
        try:
            prev_status = state.state[type][parameters]['status']
        except (IndexError,KeyError):
            #if we are here, we've never seen this event type, parameter combination before
            prev_status = None

        # if this event has never generated 'state' before, populate the defaults
        if not parameters in state.state[type]:
             state.state[type][parameters] = {'name' : config.ZONENAMES[parameters] if type == 'zone' else config.PARTITIONNAMES[parameters], 'lastevents' : [], 'status' : defaultStatus}

        #update the state
        state.state[type][parameters]['status'] = dict(state.state[type][parameters]['status'], **event['status'])

        #if this is the first event in this zone/partition we've seen, don't do anything here.
        if prev_status != None:
            #if we've seen this before, check if it's changed
            if prev_status == state.state[type][parameters]['status']:
                logger.debug('Discarded event. State not changed. ({} {})'.format(event['type'], parameters))
            else:
                events.put('statechange', type, parameters, code, event, message, defaultStatus)

        #write event
        state.state[type][parameters]['lastevents'].append({  
                  'datetime' : str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), 
                  'code'     : code,
                  'message'  : message})

        #write to all events
        state.state[type]['lastevents'].append({  
                  'datetime' : str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), 
                  'code'     : code,
                  'message'  : message})
