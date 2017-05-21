"""Config Module"""
#pylint: disable=R0901,R0904
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
from core import logger

class Config(configparser.ConfigParser):
    """Config class"""
    def __init__(self, configfile='alarmserver.cfg', maxpartitions=16,
                 maxzones=128, maxalarmusers=47):
        self.maxpartitions = maxpartitions
        self.maxzones = maxzones
        self.maxalarmusers = maxalarmusers
        logger.debug('Loading config file: %s' % configfile)
        super(Config, self).__init__()
        self.read(configfile)

    def get_val(self, section, variable, default, var_type='str'):
        """Read configuration variable"""
        try:
            if var_type == 'str':
                ret = self.get(section, variable)
            elif var_type == 'bool':
                ret = self.getboolean(section, variable)
            elif var_type == 'int':
                ret = int(self.get(section, variable))
            elif var_type == 'list':
                ret = self.get(section, variable).split(",")
            elif var_type == 'listint':
                ret = [int(i) for i in self.get(section, variable).split(",")]
        except (configparser.NoSectionError, configparser.NoOptionError):
            ret = default

        # If the variable is empty, return the default
        if ret == "":
            ret = default

        return ret

    # LOGGING
    @property
    def logfile(self):
        """Return logfile from config"""
        return self.get_val('alarmserver', 'logfile', '', 'str')

    @property
    def logurlrequests(self):
        """Return logurlrequests from config"""
        return self.get_val('alarmserver', 'logurlrequests', True, 'bool')

    # HTTP
    @property
    def http(self):
        """Return https from config"""
        return self.get_val('alarmserver', 'http', True, 'bool')

    @property
    def httpport(self):
        """Return httpsport from config"""
        return self.get_val('alarmserver', 'httpport', 8011, 'int')

    # HTTPS
    @property
    def https(self):
        """Return https from config"""
        return self.get_val('alarmserver', 'https', True, 'bool')

    @property
    def httpsport(self):
        """Return httpsport from config"""
        return self.get_val('alarmserver', 'httpsport', 8111, 'int')

    @property
    def certfile(self):
        """Return certfile from config"""
        return self.get_val('alarmserver', 'certfile', 'server.crt', 'str')

    @property
    def keyfile(self):
        """Return keyfile from config"""
        return self.get_val('alarmserver', 'keyfile', 'server.key', 'str')

    # Web auth
    @property
    def webauthuser(self):
        """Return webauthuser from config"""
        return self.get_val('alarmserver', 'webauthuser', False, 'str')

    @property
    def webauthpass(self):
        """Return webauthpass from config"""
        return self.get_val('alarmserver', 'webauthpass', False, 'str')

    # Events
    @property
    def maxevents(self):
        """Return maxevents from config"""
        return self.get_val('alarmserver', 'maxevents', 10, 'int')

    @property
    def maxallevents(self):
        """Return maxallevents from config"""
        return self.get_val('alarmserver', 'maxallevents', 100, 'int')

    # This should be an envisalink property
    @property
    def enableproxy(self):
        """Return enableproxy from config"""
        return self.get_val('alarmserver', 'enableproxy', True, 'bool')

    # Envisalink
    @property
    def envisalinkhost(self):
        """Return envisalinkhost from config"""
        return self.get_val('envisalink', 'host', 'envisalink', 'str')

    @property
    def envisalinkport(self):
        """Return envisalinkport from config"""
        return self.get_val('envisalink', 'port', 4025, 'int')

    @property
    def envisalinkpass(self):
        """Return envisalinkpass from config"""
        return self.get_val('envisalink', 'pass', 'user', 'str')

    @property
    def envisalinkkeepalive(self):
        """Return envisalinkkeepalive from config"""
        return self.get_val('envisalink', 'keepalive', 60, 'int')

    @property
    def envisalinklograw(self):
        """Return envisalinklograw from config"""
        return self.get_val('envisalink', 'lograwmessage', False, 'bool')

    @property
    def envisalinkproxyport(self):
        """Return envisalinkproxyport from config"""
        return self.get_val('envisalink', 'proxyport', self.envisalinkport, 'int')

    @property
    def envisalinkproxypass(self):
        """Return envisalinkproxypass from config"""
        return self.get_val('envisalink', 'proxypass', self.envisalinkpass, 'str')

    @property
    def alarmcode(self):
        """Return alarmcode from config"""
        return self.get_val('envisalink', 'alarmcode', 1111, 'int')

    @property
    def eventtimeago(self):
        """Return eventtimeago from config"""
        return self.get_val('envisalink', 'eventtimeago', True, 'bool')

    @property
    def partitionnames(self):
        """Return partitionnames from config"""
        ret = {}
        for i in range(1, self.maxpartitions+1):
            partition = self.get_val('alarmserver', 'partition{}'.format(i), False, 'str')
            if partition:
                ret[i] = partition
        return ret

    @property
    def zonenames(self):
        """Return zonenames from config"""
        ret = {}
        for i in range(1, self.maxzones+1):
            zone = self.get_val('alarmserver', 'zone{}'.format(i), False, 'str')
            if zone:
                ret[i] = zone
        return ret

    @property
    def alarmusernames(self):
        """Return alarmusernames from config"""
        ret = {}
        for i in range(1, self.maxalarmusers+1):
            user = self.get_val('alarmserver', 'user{}'.format(i), False, 'str')
            if user:
                ret[i] = user
        return ret
