from typing import Any

import simplejson as json
from werkzeug.exceptions import BadRequest as BaseBadRequest
from werkzeug.exceptions import Forbidden as BaseForbidden
from werkzeug.exceptions import HTTPException as BaseHTTPException
from werkzeug.exceptions import InternalServerError as BaseInternalServerError
from werkzeug.exceptions import MethodNotAllowed as BaseMethodNotAllowed
from werkzeug.exceptions import NotFound as BaseNotFound
from werkzeug.exceptions import Unauthorized as BaseUnauthorized

from openslides_backend.shared.exceptions import ViewException


class HTTPException(BaseHTTPException):
    def __init__(
        self, view_exception: ViewException | None = None, *args: Any, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.view_exception = view_exception

    def get_body(
        self, environ: dict[str, Any] | None = None, scope: dict | None = None
    ) -> str:
        if hasattr(self, "view_exception") and self.view_exception:
            return json.dumps(self.view_exception.get_json())
        else:
            return json.dumps(
                {
                    "success": False,
                    "message": self.description,
                }
            )

    def get_headers(
        self,
        environ: dict[str, Any] | None = None,
        scope: dict | None = None,
    ) -> list[tuple[str, str]]:
        return [("Content-Type", "application/json")]


class BadRequest(HTTPException, BaseBadRequest):
    pass


class Forbidden(HTTPException, BaseForbidden):
    pass


class Unauthorized(HTTPException, BaseUnauthorized):
    pass


class MethodNotAllowed(HTTPException, BaseMethodNotAllowed):
    pass


class NotFound(HTTPException, BaseNotFound):
    pass


class InternalServerError(HTTPException, BaseInternalServerError):
    pass
