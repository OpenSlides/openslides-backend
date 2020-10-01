from .base import BasePresenterTestCase


class ServerTimeTest(BasePresenterTestCase):
    def test_server_time(self) -> None:
        status_code, data = self.request("server_time")
        self.assertEqual(status_code, 200)
        assert data.get("server_time") is not None
        assert isinstance(data["server_time"], int)
        assert data["server_time"] > 1601468054
