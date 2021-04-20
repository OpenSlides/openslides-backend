from openslides_backend.permissions.permissions import Permissions

from .base import BasePresenterTestCase

TEST_USER_PW = "test"


class TestGetForwardingMeetings(BasePresenterTestCase):
    def test_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "meeting1", "committee_id": 2},
                "meeting/2": {"name": "meeting2", "committee_id": 3},
                "committee/2": {
                    "name": "com2",
                    "forward_to_committee_ids": [3],
                    "meeting_ids": [1],
                },
                "committee/3": {
                    "name": "com3",
                    "meeting_ids": [2],
                },
            }
        )
        status_code, data = self.request("get_forwarding_meetings", {"meeting_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data,
            [
                {
                    "id": 3,
                    "name": "com3",
                    "meetings": [{"id": 2, "name": "meeting2"}],
                }
            ],
        )

    def test_no_permissions(self) -> None:
        self.set_models(
            {
                "user/3": {
                    "username": "test",
                    "is_active": True,
                    "default_password": TEST_USER_PW,
                    "password": self.auth.hash(TEST_USER_PW),
                    "group_$3_ids": [3],
                },
                "meeting/3": {"group_ids": [3]},
                "group/3": {"meeting_id": 3},
            }
        )
        self.client.login("test", TEST_USER_PW)
        status_code, data = self.request("get_forwarding_meetings", {"meeting_id": 3})
        assert status_code == 403
        assert "Missing permission" in data["message"]

    def test_complex(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "meeting1", "committee_id": 2, "group_ids": [2]},
                "meeting/2": {"name": "meeting2", "committee_id": 3, "group_ids": [3]},
                "meeting/3": {"committee_id": 3, "group_ids": [4]},
                "committee/2": {
                    "name": "com2",
                    "forward_to_committee_ids": [3],
                    "meeting_ids": [1],
                },
                "committee/3": {
                    "name": "com3",
                    "meeting_ids": [2, 3],
                },
                "user/3": {
                    "username": "test",
                    "is_active": True,
                    "default_password": TEST_USER_PW,
                    "password": self.auth.hash(TEST_USER_PW),
                    "group_$1_ids": [2],
                    "group_$2_ids": [3],
                    "group_$3_ids": [4],
                },
                "group/2": {
                    "meeting_id": 1,
                    "permissions": [Permissions.Motion.CAN_MANAGE],
                },
                "group/3": {
                    "meeting_id": 2,
                    "permissions": [Permissions.Motion.CAN_CREATE],
                },
                "group/4": {
                    "meeting_id": 3,
                    "permissions": [],
                },
            }
        )
        self.client.login("test", TEST_USER_PW)
        status_code, data = self.request("get_forwarding_meetings", {"meeting_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data,
            [
                {
                    "id": 3,
                    "name": "com3",
                    "meetings": [{"id": 2, "name": "meeting2"}],
                }
            ],
        )
