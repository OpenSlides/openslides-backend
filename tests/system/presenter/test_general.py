from .base import PRESENTER_URL, BasePresenterTestCase


class GeneralPresenterWSGITester(BasePresenterTestCase):
    def test_request_wrong_method(self) -> None:
        response = self.client.get(PRESENTER_URL)
        self.assert_status_code(response, 405)

    def test_request_wrong_media_type(self) -> None:
        response = self.client.post(PRESENTER_URL)
        self.assert_status_code(response, 400)
        self.assertIn("Wrong media type.", response.json["message"])

    def test_request_missing_body(self) -> None:
        response = self.client.post(PRESENTER_URL, content_type="application/json")
        self.assert_status_code(response, 400)
        self.assertIn("Failed to decode JSON object", response.json["message"])

    def test_request_empty(self) -> None:
        response = self.client.post(PRESENTER_URL, json=[{"presenter": ""}])
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0].presenter must be longer than or equal to 1 characters",
            response.json["message"],
        )

    def test_request_fuzzy(self) -> None:
        response = self.client.post(
            PRESENTER_URL,
            json=[{"presenter": "non_existing_presenter"}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Presenter non_existing_presenter does not exist.",
            response.json["message"],
        )
