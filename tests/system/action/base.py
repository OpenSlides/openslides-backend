from typing import Any, Dict, List

from openslides_backend.shared.interfaces.wsgi import WSGIApplication
from tests.system.base import BaseSystemTestCase
from tests.system.util import create_action_test_application


class BaseActionTestCase(BaseSystemTestCase):
    def get_application(self) -> WSGIApplication:
        return create_action_test_application()

    def request(self, action: str, data: Dict[str, Any]) -> Any:
        return self.request_multi(action, [data])

    def request_multi(self, action: str, data: List[Dict[str, Any]]) -> Any:
        return self.client.post(
            "/",
            json=[
                {
                    "action": action,
                    "data": data,
                }
            ],
        )
