from typing import Any, Dict, Optional, Tuple

import simplejson as json

from openslides_backend.shared.interfaces.wsgi import WSGIApplication
from tests.system.base import BaseSystemTestCase
from tests.system.util import create_presenter_test_application


class BasePresenterTestCase(BaseSystemTestCase):
    def get_application(self) -> WSGIApplication:
        return create_presenter_test_application()

    def request(
        self, presenter: str, data: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Requests a single presenter and returns the status code and the json decoded
        response. Automatically removes array around response data.
        """
        payload: Dict[str, Any] = {"presenter": presenter}
        if data:
            payload["data"] = data
        response = self.client.post("/", json=[payload])
        return (response.status_code, json.loads(response.data)[0])
