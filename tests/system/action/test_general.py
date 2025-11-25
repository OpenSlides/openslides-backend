

from openslides_backend.http.views.action_view import ActionView
from tests.system.util import get_route_path

from .base import ACTION_URL, BaseActionTestCase
from .util import get_internal_auth_header


class GeneralActionWSGITester(BaseActionTestCase):
    """
    Tests the action WSGI application in general.
    """

    def test_request_wrong_method(self) -> None:
        response = self.client.get(ACTION_URL)
        self.assert_status_code(response, 405)

    def test_request_wrong_media_type(self) -> None:
        response = self.client.post(ACTION_URL)
        self.assert_status_code(response, 400)
        self.assertIn("Wrong media type.", response.json["message"])

    def test_request_missing_body(self) -> None:
        response = self.client.post(ACTION_URL, content_type="application/json")
        self.assert_status_code(response, 400)
        self.assertIn("Failed to decode JSON object", response.json["message"])

    def test_request_fuzzy_body(self) -> None:
        response = self.client.post(
            ACTION_URL,
            json={"fuzzy_key_Eeng7pha3a": "fuzzy_value_eez3Ko6quu"},
        )
        self.assert_status_code(response, 400)
        self.assertIn("data must be array", response.json["message"])

    def test_request_fuzzy_body_2(self) -> None:
        response = self.client.post(
            ACTION_URL,
            json=[{"fuzzy_key_Voh8in7aec": "fuzzy_value_phae3iew4W"}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain ['action', 'data'] properties",
            response.json["message"],
        )

    def test_request_no_existing_action(self) -> None:
        response = self.request("fuzzy_action_hamzaeNg4a", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Action fuzzy_action_hamzaeNg4a does not exist.",
            response.json["message"],
        )

    def test_request_handle_separately(self) -> None:
        response = self.client.post(
            get_route_path(ActionView.action_route, "handle_separately"), json=[{}]
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain ['action', 'data'] properties",
            response.json["message"],
        )

    def test_migrations_route(self) -> None:
        response = self.client.post(
            get_route_path(ActionView.migrations_route),
            json={"cmd": "stats"},
            headers=get_internal_auth_header(),
        )
        self.assert_status_code(response, 200)

    def test_health_route(self) -> None:
        response = self.client.get(get_route_path(ActionView.health_route))
        self.assert_status_code(response, 200)

    def test_info_route(self) -> None:
        response = self.client.get(get_route_path(ActionView.info_route))
        self.assert_status_code(response, 200)
        self.assertIn("healthinfo", response.json)
        actions = response.json["healthinfo"]["actions"]
        some_example_actions = (
            "topic.create",
            "motion.delete",
        )
        for action in some_example_actions:
            self.assertIn(action, actions.keys())
