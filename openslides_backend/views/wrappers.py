from werkzeug.wrappers import Request as WerkzeugRequest
from werkzeug.wrappers.json import JSONMixin  # type: ignore


class Request(JSONMixin, WerkzeugRequest):
    """
    Customized Request to use the JSONMixin.
    """

    pass
