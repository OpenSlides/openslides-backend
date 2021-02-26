from werkzeug.wrappers import Request as WerkzeugRequest
from werkzeug.wrappers.json import JSONMixin


class Request(JSONMixin, WerkzeugRequest):
    """
    Customized request object. We use the JSONMixin here.
    """
