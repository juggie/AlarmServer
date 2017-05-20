"""Config Module"""
import configparser
from core import logger

MAXPARTITIONS = 16
MAXZONES = 128
MAXALARMUSERS = 47

class Config():
    """Config class"""
    @staticmethod
    def load(configfile):
        """Load config file"""
        logger.debug('Loading config file: %s' % configfile)
        Config._config = configparser.ConfigParser()

        if Config._config.read(configfile) == []:
            raise RuntimeError('Unable to load config file: %s' % configfile)

        Config.LOGURLREQUESTS = Config.read_config_var('alarmserver', 'logurlrequests', \
            True, 'bool')
        Config.HTTPSPORT = Config.read_config_var('alarmserver', 'httpsport', 8111, 'int')
        Config.HTTPS = Config.read_config_var('alarmserver', 'https', True, 'bool')
        Config.CERTFILE = Config.read_config_var('alarmserver', 'certfile', 'server.crt', 'str')
        Config.KEYFILE = Config.read_config_var('alarmserver', 'keyfile', 'server.key', 'str')
        Config.HTTPPORT = Config.read_config_var('alarmserver', 'httpport', 8011, 'int')
        Config.HTTP = Config.read_config_var('alarmserver', 'http', False, 'bool')
        Config.WEBAUTHUSER = Config.read_config_var('alarmserver', 'webauthuser', False, 'str')
        Config.WEBAUTHPASS = Config.read_config_var('alarmserver', 'webauthpass', False, 'str')
        Config.MAXEVENTS = Config.read_config_var('alarmserver', 'maxevents', 10, 'int')
        Config.MAXALLEVENTS = Config.read_config_var('alarmserver', 'maxallevents', 100, 'int')
        Config.ENVISALINKHOST = Config.read_config_var('envisalink', 'host', 'envisalink', 'str')
        Config.ENVISALINKPORT = Config.read_config_var('envisalink', 'port', 4025, 'int')
        Config.ENVISALINKPASS = Config.read_config_var('envisalink', 'pass', 'user', 'str')
        Config.ENVISALINKKEEPALIVE = Config.read_config_var('envisalink', 'keepalive', \
            60, 'int')
        Config.ENVISALINKLOGRAW = Config.read_config_var('envisalink', \
            'lograwmessage', False, 'bool')
        Config.ENABLEPROXY = Config.read_config_var('envisalink', \
            'enableproxy', True, 'bool')
        Config.ENVISALINKPROXYPORT = Config.read_config_var('envisalink', \
            'proxyport', Config.ENVISALINKPORT, 'int')
        Config.ENVISALINKPROXYPASS = Config.read_config_var('envisalink', \
            'proxypass', Config.ENVISALINKPASS, 'str')
        Config.ALARMCODE = Config.read_config_var('envisalink', 'alarmcode', 1111, 'int')
        Config.EVENTTIMEAGO = Config.read_config_var('alarmserver', 'eventtimeago', True, 'bool')
        Config.LOGFILE = Config.read_config_var('alarmserver', 'logfile', '', 'str')
        if Config.LOGFILE == '':
            Config.LOGTOFILE = False
        else:
            Config.LOGTOFILE = True

        Config.PARTITIONNAMES = {}
        for i in range(1, MAXPARTITIONS+1):
            partition = Config.read_config_var('alarmserver', 'partition'+str(i), \
                False, 'str', True)
            if partition:
                Config.PARTITIONNAMES[i] = partition

        Config.ZONENAMES = {}
        for i in range(1, MAXZONES+1):
            zone = Config.read_config_var('alarmserver', 'zone'+str(i), False, 'str', True)
            if zone:
                Config.ZONENAMES[i] = zone

        Config.ALARMUSERNAMES = {}
        for i in range(1, MAXALARMUSERS+1):
            user = Config.read_config_var('alarmserver', 'user'+str(i), False, 'str', True)
            if user:
                Config.ALARMUSERNAMES[i] = user

    @staticmethod
    def defaulting(section, variable, default, quiet=False):
        """Defaulting"""
        if not quiet:
            logger.debug('Config option '+ str(variable) + ' not set in ['+\
                str(section)+'] defaulting to: \''+str(default)+'\'')

    @staticmethod
    def read_config_var(section, variable, default, var_type='str', quiet=False):
        """Read configuration variable"""
        try:
            if var_type == 'str':
                return Config._config.get(section, variable)
            elif var_type == 'bool':
                return Config._config.getboolean(section, variable)
            elif var_type == 'int':
                return int(Config._config.get(section, variable))
            elif var_type == 'list':
                return Config._config.get(section, variable).split(",")
            elif var_type == 'listint':
                return [int(i) for i in Config._config.get(section, variable).split(",")]
        except (configparser.NoSectionError, configparser.NoOptionError):
            Config.defaulting(section, variable, default, quiet)
            return default
