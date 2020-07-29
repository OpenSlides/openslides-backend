import json

from openslides_backend.presenter import PresenterBlob

from .test_base import BasePresenterUnitTester, BasePresenterWSGITester


class WhoamiUnitTester(BasePresenterUnitTester):
    def test_unit_whoami(self) -> None:
        payload = [PresenterBlob(presenter="whoami")]
        response = self.presenter_handler.handle_request(
            payload=payload, user_id=self.user_id,
        )
        expected = [
            {
                "auth_type": "default",
                "permissions": [],
                "user_id": 1,
                "guest_enabled": True,
                "groups_id": [2],
                "short_name": "username",
            }
        ]
        self.assertEqual(response, expected)


class WhoamiWSGITester(BasePresenterWSGITester):
    def test_wsgi_whoami(self) -> None:
        response = self.client.get("/", json=[{"presenter": "whoami"}])
        self.assertEqual(response.status_code, 200)
        expected = [
            {
                "auth_type": "default",
                "permissions": [],
                "user_id": 1,
                "guest_enabled": True,
                "groups_id": [2],
                "short_name": "username",
            }
        ]
        self.assertEqual(json.loads(response.data), expected)
