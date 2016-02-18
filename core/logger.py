import logging, inspect
import sys
from os import path

#class to dispatch our log events
class DispatchingFormatter:
    def __init__(self, formatters, default_formatter):
        self._formatters = formatters
        self._default_formatter = default_formatter

    def format(self, record):
        formatter = self._formatters.get(record.name, self._default_formatter)
        return formatter.format(record)

#setup logging handler
handler = logging.StreamHandler()

#set the formatter as our dispatching class
handler.setFormatter(DispatchingFormatter({
        'alarmserver': logging.Formatter('%(asctime)s - %(levelname)s - %(s_filename)s:%(s_function_name)s@%(s_line_number)s: %(message)s', '%b %d %H:%M:%S')
    },
    logging.Formatter('%(asctime)s - %(levelname)s: %(message)s', '%b %d %H:%M:%S'),
))
#setup our handler and log level
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.DEBUG)

#set the root path of our scrippt
rootpath = path.dirname(path.abspath(sys.modules['__main__'].__file__)) + '/'

#logging functions
def error(message):
    write(logging.ERROR, message)

def debug(message):
    write(logging.DEBUG, message)

def warning(message):
    write(logging.WARNING, message)

def info(message):
    write(logging.INFO, message)

def write(level, message):
    (frame, filename, line_number, function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[2]
    if filename  == __file__:
        (frame, filename, line_number, function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[3]
    logging.getLogger('alarmserver').log(level, message, extra={'s_filename' : filename.replace(rootpath, ''), 's_line_number' : line_number, 's_function_name' : function_name})
