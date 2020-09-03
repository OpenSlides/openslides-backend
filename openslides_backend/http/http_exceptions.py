import json
from typing import Any, Dict, List, Optional, Tuple

from werkzeug.exceptions import BadRequest as BaseBadRequest
from werkzeug.exceptions import Forbidden as BaseForbidden
from werkzeug.exceptions import HTTPException as BaseHTTPException
from werkzeug.exceptions import MethodNotAllowed as BaseMethodNotAllowed


class HTTPException(BaseHTTPException):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__()
        self.message = message

    def get_body(self, environ: Optional[Dict[str, Any]] = None) -> str:
        return json.dumps(
            {
                "success": False,
                "message": self.message
                if hasattr(self, "message") and self.message
                else self.description,
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
