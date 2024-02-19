from openslides_backend.http.views.action_view import ActionView
from tests.system.action.base import BaseActionTestCase
from tests.system.util import get_route_path


class TestVersionRoute(BaseActionTestCase):
    def test_version_route(self) -> None:
        path = get_route_path(ActionView.version_route)
        response = self.anon_client.get(path)
        self.assert_status_code(response, 200)
        assert response.json == {"version": "dev"}
