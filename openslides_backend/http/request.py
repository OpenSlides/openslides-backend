from typing import Any

from werkzeug.wrappers import Request as WerkzeugRequest

from .http_exceptions import BadRequest


class Request(WerkzeugRequest):
    """
    Customized request object to make sure a value is returned by json().
    """

    @property
    def json(self) -> Any:
        if json := self.get_json():
            return json
        raise BadRequest()
