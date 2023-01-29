"""Alarmserver state machine"""
#pylint: disable=R0201
import datetime

#alarmserver modules
from . import logger
from .events import Events

class State():
    """State class"""
    logger.debug('State Module Loaded')

    @staticmethod
    def init(config):
        """Init"""
        State.config = config
        State.state = {}
        Events.register('alarm', State.update)

    @staticmethod
    def get_dict():
        """Return dict of state"""
        return State.state

    @staticmethod
    def set_version(version):
        """Set version"""
        State.state['version'] = version

    @staticmethod
    def update(event_type, type, parameters, code, event, message, default_status):
        """Update state machine"""
        if not type in State.state:
            State.state[type] = {'lastevents' : []}

        #keep the last state
        try:
            prev_status = State.state[type][parameters]['status']
        except (IndexError, KeyError):
            #if we are here, we've never seen this event type, parameter combination before
            prev_status = None

        # if this event has never generated 'state' before, populate the defaults
        if not parameters in State.state[type]:
            State.state[type][parameters] = {
                'name' : State.config.zonenames[parameters]
                         if type == 'zone' else State.config.partitionnames[parameters],
                'lastevents' : [], 'status' : default_status}

        #update the state
        State.state[type][parameters]['status'] = dict(State.state[type][parameters]['status'],
                                                       **event['status'])

        #if this is the first event in this zone/partition we've seen, don't do anything here.
        if prev_status != None:
            #if we've seen this before, check if it's changed
            if prev_status == State.state[type][parameters]['status']:
                logger.debug('Discarded event. State not changed. ({} {})'.format(event['type'],
                                                                                  parameters))
            else:
                Events.put('statechange', type, parameters, code, event, message, defaultStatus)
        else:
            Events.put('stateinit', type, parameters, code, event, message, defaultStatus)

        #write event
        State.state[type][parameters]['lastevents'].append({
            'datetime' : str(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")),
            'code'     : code,
            'message'  : message})

        #write to all events
        State.state[type]['lastevents'].append({
            'datetime' : str(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")),
            'code'     : code,
            'message'  : message})
