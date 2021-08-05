from .base import BasePresenterTestCase


class TestCheckMediafileId(BasePresenterTestCase):
    def test_simple(self) -> None:
        self.create_model(
            "mediafile/1", {"filename": "the filename", "is_directory": False}
        )
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"ok": True, "filename": "the filename"})

    def test_is_directory(self) -> None:
        self.create_model(
            "mediafile/1", {"filename": "the filename", "is_directory": True}
        )
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"ok": False})

    def test_non_existent(self) -> None:
        payload = {"presenter": "check_mediafile_id", "data": {"mediafile_id": 1}}
        response = self.client.post("/", json=[payload])
        self.assert_status_code(response, 400)

    def test_request_without_token(self) -> None:
        self.create_model(
            "mediafile/1", {"filename": "the filename", "is_directory": False}
        )
        self.client.headers = {}
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"ok": True, "filename": "the filename"})
