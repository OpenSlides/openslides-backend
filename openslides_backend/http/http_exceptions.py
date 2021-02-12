import json
from typing import Any, Dict, List, Optional, Tuple

from werkzeug.exceptions import BadRequest as BaseBadRequest
from werkzeug.exceptions import Forbidden as BaseForbidden
from werkzeug.exceptions import HTTPException as BaseHTTPException
from werkzeug.exceptions import MethodNotAllowed as BaseMethodNotAllowed

from openslides_backend.shared.exceptions import ViewException


class HTTPException(BaseHTTPException):
    def __init__(self, view_exception: Optional[ViewException] = None) -> None:
        super().__init__()
        self.view_exception = view_exception

    def get_body(self, environ: Optional[Dict[str, Any]] = None) -> str:
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
        self, environ: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, str]]:
        return [("Content-Type", "application/json")]


class BadRequest(BaseBadRequest, HTTPException):
    pass


class Forbidden(BaseForbidden, HTTPException):
    pass


class MethodNotAllowed(BaseMethodNotAllowed, HTTPException):
    pass
