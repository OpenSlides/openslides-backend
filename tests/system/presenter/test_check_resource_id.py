from .base import BasePresenterTestCase


class TestCheckMediafileId(BasePresenterTestCase):
    def test_simple(self) -> None:
        self.create_model(
            "resource/1", {"token": "the filename", "mimetype": "text/plain"}
        )
        status_code, data = self.request("check_resource_id", {"resource_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"ok": True, "filename": "the filename.txt"})

    def test_non_existent(self) -> None:
        payload = {"presenter": "check_resource_id", "data": {"resource_id": 1}}
        response = self.client.post("/", json=[payload])
        self.assert_status_code(response, 400)
