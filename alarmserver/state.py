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
    def updateZone(code, zone, event, message, defaultStatus):
        if not 'zone' in state.state: state.state['zone'] = {'lastevents' : []}

        # if the zone is named in the config file save info in state.state
        if zone in config.ZONENAMES:
            # save zone if not already there
            if not zone in state.state['zone']:
                state.state['zone'][zone] = {'name' : config.ZONENAMES[zone], 'lastevents' : [], 'status' : defaultStatus}
        else:
            logger.debug('Ignoring unnamed zone {}'.format(zone))

        try:
            #keep the last state
            prev_status = state.state['zone'][zone]['status']
            #update the state
            state.state['zone'][zone]['status'] = dict(state.state['zone'][zone]['status'], **event['status'])
            #is the state changed?
            if prev_status == state.state['zone'][zone]['status']:
                logger.debug('Discarded event. State not changed. ({} {})'.format(event['type'], zone))
        except KeyError:
            pass

    @staticmethod
    def updatePartition(code, partition, event, message, defaultStatus):
        if not 'partition' in state.state: state.state['partition'] = {'lastevents' : []}

        # if the partition is named in the config file save info in state.state
        if partition in config.PARTITIONNAMES:
            # save partition if not already there
            if not partition in state.state['partition']:
                state.state['partition'][partition] = {'name' : config.PARTITIONNAMES[partition], 'lastevents' : [], 'status' : defaultStatus}
        else:
            logger.debug('Ignoring unnamed partition {}'.format(partition))

        try:
            #keep the last state
            prev_status = state.state['partition'][partition]['status']
            #update the state
            state.state['partition'][partition]['status'] = dict(state.state['partition'][partition]['status'], **event['status'])
            #is the state changed?
            if prev_status == state.state['partition'][partition]['status']:
                logger.debug('Discarded event. State not changed. ({} {})'.format(event['type'], partition))
        except KeyError:
            pass
