import json

from flask import Response

from openslides_backend.shared.typing import JSON


class JsonResponse(Response):
    def __init__(self, obj: JSON, status_code: int = 200) -> None:
        super().__init__(
            self.dumps(obj), status=status_code, mimetype="application/json"
        )

    def dumps(self, obj: JSON) -> str:
        return json.dumps(obj, indent=None, separators=(",", ":"))
