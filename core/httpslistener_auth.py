import logger, base64, hashlib
from config import config

class InvalidLogin(Exception):
    pass

def require_basic_auth(handler_class):
    def wrap_execute(handler_execute):
        def require_basic_auth(handler, kwargs):
            try:
                auth_header = handler.request.headers.get('Authorization')
                username, password = base64.decodestring(auth_header[6:]).split(':', 2)
                if config.WEBAUTHUSER == False and config.WEBAUTHPASS == False:
                    return True
                elif config.WEBAUTHUSER == False or config.WEBAUTHPASS == False:
                    logger.debug('Auth disabled as either user was set w/o pass, or pass was set w/o user')
                    return True
                elif username == config.WEBAUTHUSER and hashlib.sha1(password).hexdigest() == config.WEBAUTHPASS:
                    return True
                else:
                    raise InvalidLogin
            except (TypeError, InvalidLogin):
                handler.set_status(401)
                handler.set_header('WWW-Authenticate', 'Basic realm=AlarmServer')
                handler._transforms = []
                handler.finish()
                return False

        def _execute(self, transforms, *args, **kwargs):
            if not require_basic_auth(self, kwargs):
                return False
            return handler_execute(self, transforms, *args, **kwargs)
        return _execute

    handler_class._execute = wrap_execute(handler_class._execute)
    return handler_class

