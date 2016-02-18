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
        state.oldstate = {}
        events.register('zone', state.update)
        events.register('partition', state.update)


    @staticmethod
    def getDict():
        return state.state

    @staticmethod
    def setVersion(version):
        state.state['version'] = version

    @staticmethod
    def update(type, code, parameters, event, message, defaultStatus):
        if not type in state.state: state.state[type] = {'lastevents' : []}

        # if the zone/partition is named in the config file save info in state.state
        if (type == 'zone' and parameters in config.ZONENAMES) or (type == 'partition' and parameters in config.PARTITIONNAMES):
            if not parameters in state.state[type]:
                state.state[type][parameters] = {'name' : config.ZONENAMES[parameters] if type == 'zone' else config.PARTITIONNAMES[parameters], 'lastevents' : [], 'status' : defaultStatus}
        else:
            logger.debug('Ignoring unnamed %s %s' % (type, parameters))
            return

        try:
            #keep the last state
            prev_status = state.state[type][parameters]['status']
            #update the state
            state.state[type][parameters]['status'] = dict(state.state[type][parameters]['status'], **event['status'])
            #is the state changed?
            if prev_status == state.state[type][parameters]['status']:
                logger.debug('Discarded event. State not changed. ({} {})'.format(event['type'], parameters))
        except KeyError:
            pass

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
