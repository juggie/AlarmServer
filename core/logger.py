"""This is the logger for alarmserver"""
import logging
import inspect
import sys
import os
from queue import Queue

#set the root path of our scrippt
ROOTPATH = os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__)) + '/'

class DispatchingFormatter: # pylint: disable=too-few-public-methods
    """Class to dispatch our log events"""
    def __init__(self, formatters, default_formatter):
        self._formatters = formatters
        self._default_formatter = default_formatter

    def format(self, record):
        """Method required by python logging class"""
        formatter = self._formatters.get(record.name, self._default_formatter)
        return formatter.format(record)

def start(logfile=None):
    """Start logger"""
    #setup logging handler
    if logfile:
        try:
            handler = logging.FileHandler(logfile)
        except IOError:
            handler = logging.StreamHandler()
            error("Unable to open %s for writing" % logfile)
    else:
        handler = logging.StreamHandler()

    #set the formatter as our dispatching class
    handler.setFormatter(DispatchingFormatter(
        {
            'alarmserver': logging.Formatter('%(asctime)s - %(levelname)s - %(s_filename)s:'\
                '%(s_function_name)s@%(s_line_number)s: %(message)s', '%b %d %H:%M:%S')
        },
        logging.Formatter('%(asctime)s - %(levelname)s: %(message)s', '%b %d %H:%M:%S'),
    ))

    #setup our handler and log level
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.DEBUG)
    start.started = 1
start.started = 0

#logging functions
def error(message):
    """Write an error message to log"""
    write(logging.ERROR, message)

def debug(message):
    """Write an debug message to log"""
    write(logging.DEBUG, message)

def warning(message):
    """Write an warning message to log"""
    write(logging.WARNING, message)

def info(message):
    """Write an info message to log"""
    write(logging.INFO, message)

def write(level, message):
    """Write a message to log"""
    #pylint: disable=unused-variable
    (frame, filename, line_number, function_name, lines, index) = \
        inspect.getouterframes(inspect.currentframe())[2]
    #pylint: enable=unused-variable
    if filename == __file__:
        (frame, filename, line_number, function_name, lines, index) = \
            inspect.getouterframes(inspect.currentframe())[3]
    extra = {'s_filename' : filename.replace(ROOTPATH, ''), 's_line_number' : line_number,\
        's_function_name' : function_name}
    if start.started:
        while not write.queue.empty():
            job = write.queue.get()
            logging.getLogger('alarmserver').log(job['level'], job['message'], extra=job['extra'])
        logging.getLogger('alarmserver').log(level, message, extra=extra)
    else:
        write.queue.put({'level' : level, 'message' : message, 'extra' : extra})
write.queue = Queue()
