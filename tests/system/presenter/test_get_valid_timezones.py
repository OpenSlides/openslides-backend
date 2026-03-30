from .base import BasePresenterTestCase


class TestGetValidTimezones(BasePresenterTestCase):
    def test_get(self) -> None:
        status_code, data = self.request("get_valid_timezones", {})
        self.assertEqual(status_code, 200)
        assert isinstance(data, dict)
        # Checking for Korea bc no DST, therfore just one possible abbreviation.
        assert data.get("Asia/Seoul") == "KST"
