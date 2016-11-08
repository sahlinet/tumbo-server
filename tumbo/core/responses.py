import json
import logging

logger = logging.getLogger(__name__)

ACTION_RESTART = "RESTART"


class Response(object):

    def __init__(self, content, **kwargs):
        if hasattr(self, "CONTENT_TYPE"):
            self.content_type = self.CONTENT_TYPE
        else:
            self.content_type = None
        self.content = content
        self.status_code = kwargs.get("status_code", 200)

        self.action = kwargs.get("action", None)
        if self.action:
            logger.debug("Action %s" % self.action)

    def serialize(self):
        d = {'content_type': self.content_type,
                'content': self.content,
                'class': self.__class__.__name__,
                'status_code': self.status_code
        }
        if self.action:
            logger.warn("Action %s" % self.action)
            d['action'] = self.action
        return d

    def __str__(self):
        return json.dumps(self.serialize())

class XMLResponse(Response):
    CONTENT_TYPE = "application/xml"

class HTMLResponse(Response):
    CONTENT_TYPE = "text/html"

class JSONResponse(Response):
    CONTENT_TYPE = "application/json"

class RedirectResponse(Response):
    pass
