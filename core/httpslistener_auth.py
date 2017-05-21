"""http auth wrappers"""
#pylint: disable=W0621,W0212

import base64
import hashlib
from functools import wraps
from . import logger

class InvalidLogin(Exception):
    """Invalid Login Exception"""
    pass

def require_basic_auth(handler_class):
    """Require basic auth wrapper"""
    def wrap_execute(handler_execute):
        """Wrap execute"""
        @wraps(handler_execute)
        #pylint: disable=W0613
        def require_basic_auth(handler, kwargs):
            """Require basic auth wrapper"""
        #pylint: enable=W0613
            config = handler.config
            try:
                if not config.webauthuser and not config.webauthpass:
                    return True
                elif not config.webauthuser or not config.webauthpass:
                    logger.debug('Auth disabled as either user was set w/o pass,'
                                 'or pass was set w/o user')
                    return True

                auth_header = handler.request.headers.get('Authorization')
                username, password = base64.decodebytes(auth_header[6:]).split(':', 2)
                if (username == config.webauthuser and
                        hashlib.sha1(password).hexdigest() == config.webauthpass):
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
