import datetime

#alarmserver modules
import logger
from config import config

class state():
    logger.debug('State Module Loaded')

    @staticmethod
    def init():
        state.state = {}
        state.oldstate = {}

    @staticmethod
    def getDict():
        return state.state

    @staticmethod
    def setVersion(version):
        state.state['version'] = version

    #TODO: combine the update methods somehow perhaps if it can be done cleanly.
    @staticmethod
    def update(type, code, parameter, event, message, defaultStatus):
        if not type in state.state: state.state[type] = {'lastevents' : []}

        # if the zone/partition is named in the config file save info in state.state
        if (type == 'zone' and parameter in config.ZONENAMES) or (type == 'partition' and parameter in config.PARTITIONNAMES):
            if not parameter in state.state[type]:
                state.state[type][parameter] = {'name' : config.ZONENAMES[parameter] if type == 'zone' else config.PARTITIONNAMES[parameter], 'lastevents' : [], 'status' : defaultStatus}
        else:
            logger.debug('Ignoring unnamed %s %s' % (type, parameter))
            return

        try:
            #keep the last state
            prev_status = state.state[type][parameter]['status']
            #update the state
            state.state[type][parameter]['status'] = dict(state.state[type][parameter]['status'], **event['status'])
            #is the state changed?
            if prev_status == state.state[type][parameter]['status']:
                logger.debug('Discarded event. State not changed. ({} {})'.format(event['type'], parameter))
        except KeyError:
            pass

        #write event
        state.state[type][parameter]['lastevents'].append({  
                  'datetime' : str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), 
                  'code'     : code,
                  'message'  : message})

        #write to all events
        state.state[type]['lastevents'].append({  
                  'datetime' : str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), 
                  'code'     : code,
                  'message'  : message})
