from .base import BaseActionTestCase


class GeneralActionWSGITester(BaseActionTestCase):
    """
    Tests the action WSGI application in general.
    """

    def test_request_wrong_method(self) -> None:
        response = self.client.get("/")
        self.assert_status_code(response, 405)

    def test_request_wrong_media_type(self) -> None:
        response = self.client.post("/")
        self.assert_status_code(response, 400)
        self.assertIn("Wrong media type.", response.json["message"])

    def test_request_missing_body(self) -> None:
        response = self.client.post("/", content_type="application/json")
        self.assert_status_code(response, 400)
        self.assertIn("Failed to decode JSON object", response.json["message"])

    def test_request_fuzzy_body(self) -> None:
        response = self.client.post(
            "/",
            json={"fuzzy_key_Eeng7pha3a": "fuzzy_value_eez3Ko6quu"},
        )
        self.assert_status_code(response, 400)
        self.assertIn("data must be array", response.json["message"])

    def test_request_fuzzy_body_2(self) -> None:
        response = self.client.post(
            "/",
            json=[{"fuzzy_key_Voh8in7aec": "fuzzy_value_phae3iew4W"}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain ['action', 'data'] properties",
            response.json["message"],
        )

    def test_request_no_existing_action(self) -> None:
        response = self.client.post(
            "/",
            json=[{"action": "fuzzy_action_hamzaeNg4a", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Action fuzzy_action_hamzaeNg4a does not exist.",
            response.json["message"],
        )

    def test_health_route(self) -> None:
        response = self.client.get("/health")
        self.assert_status_code(response, 200)
        self.assertIn("healthinfo", response.json)
        actions = response.json["healthinfo"]["actions"]
        some_example_actions = (
            "topic.create",
            "motion.delete",
            "user.update_temporary",
        )
        for action in some_example_actions:
            self.assertIn(action, actions.keys())
