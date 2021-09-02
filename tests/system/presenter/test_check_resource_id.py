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
        status_code, data = self.request("check_resource_id", {"resource_id": 1})
        self.assertEqual(status_code, 400)
