from typing import Any, Dict, Optional, Tuple

from openslides_backend.http.views.presenter_view import PresenterView
from openslides_backend.shared.interfaces.wsgi import WSGIApplication
from tests.system.base import BaseSystemTestCase
from tests.system.util import create_presenter_test_application, get_route_path

PRESENTER_URL = get_route_path(PresenterView.presenter_route)


class BasePresenterTestCase(BaseSystemTestCase):
    def get_application(self) -> WSGIApplication:
        return create_presenter_test_application()

    def request(
        self, presenter: str, data: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, Any]:
        """
        Requests a single presenter and returns the status code and the json decoded
        response. Automatically removes array around response data.
        """
        payload: Dict[str, Any] = {"presenter": presenter}
        if data is not None:
            payload["data"] = data
        response = self.client.post(PRESENTER_URL, json=[payload])
        if isinstance(response.json, list) and len(response.json) == 1:
            return (response.status_code, response.json[0])
        return (response.status_code, response.json)
