from .base import BasePresenterTestCase


class GeneralPresenterWSGITester(BasePresenterTestCase):
    def test_request_wrong_method(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 405)

    def test_request_wrong_media_type(self) -> None:
        response = self.client.post("/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Wrong media type.", str(response.data))

    def test_request_missing_body(self) -> None:
        response = self.client.post("/", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Failed to decode JSON object", str(response.data))

    def test_request_empty(self) -> None:
        response = self.client.post("/", json=[{"presenter": ""}])
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0].presenter must be longer than or equal to 1 characters",
            str(response.data),
        )

    def test_request_fuzzy(self) -> None:
        response = self.client.post(
            "/", json=[{"presenter": "non_existing_presenter"}],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Presenter non_existing_presenter does not exist.", str(response.data),
        )
