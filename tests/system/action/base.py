from typing import Any, Dict, List

from openslides_backend.action.util.typing import Payload
from openslides_backend.shared.interfaces.wsgi import WSGIApplication
from tests.system.base import BaseSystemTestCase
from tests.system.util import create_action_test_application
from tests.util import Response


class BaseActionTestCase(BaseSystemTestCase):
    def get_application(self) -> WSGIApplication:
        return create_action_test_application()

    def request(self, action: str, data: Dict[str, Any]) -> Response:
        return self.request_multi(action, [data])

    def request_multi(self, action: str, data: List[Dict[str, Any]]) -> Response:
        response = self.request_json(
            [
                {
                    "action": action,
                    "data": data,
                }
            ]
        )
        if response.status_code == 200:
            results = response.json.get("results", [])
            assert len(results) == 1
            assert len(results[0]) == len(data)
        return response

    def request_json(self, payload: Payload) -> Response:
        return self.client.post("/", json=payload)
