import logger

class state():
    logger.debug('State Module Loaded')

    @staticmethod
    def init():
        state.state = {}

    #TODO: add proper set/get's for supported states
    @staticmethod
    def get():
        return state.state
