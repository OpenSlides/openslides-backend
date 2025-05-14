from openslides_backend.permissions.permissions import Permissions

from .base import BasePresenterTestCase

TEST_USER_PW = "test"


class TestGetForwardingMeetings(BasePresenterTestCase):
    def test_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "meeting1",
                    "committee_id": 2,
                    "is_active_in_organization_id": 1,
                },
                "meeting/2": {
                    "name": "meeting2",
                    "committee_id": 3,
                    "is_active_in_organization_id": 1,
                    "start_time": 111111,
                    "end_time": 222222,
                },
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
                    "meetings": [
                        {
                            "id": 2,
                            "name": "meeting2",
                            "start_time": 111111,
                            "end_time": 222222,
                        }
                    ],
                    "default_meeting_id": None,
                }
            ],
        )

    def test_missing_meeting_id(self) -> None:
        status_code, data = self.request("get_forwarding_meetings", {})
        self.assertEqual(status_code, 400)
        assert "data must contain ['meeting_id'] properties" == data["message"]

    def test_no_permissions(self) -> None:
        self.set_models(
            {
                "user/3": {
                    "username": "test",
                    "is_active": True,
                    "default_password": TEST_USER_PW,
                    "password": self.auth.hash(TEST_USER_PW),
                    "meeting_user_ids": [3],
                },
                "meeting_user/3": {
                    "meeting_id": 3,
                    "user_id": 3,
                    "group_ids": [3],
                },
                "meeting/3": {"group_ids": [3], "committee_id": 1},
                "committee/1": {"meeting_ids": [1]},
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
                "meeting/1": {
                    "name": "meeting1",
                    "committee_id": 2,
                    "group_ids": [2],
                    "is_active_in_organization_id": 1,
                },
                "meeting/2": {
                    "name": "meeting2",
                    "committee_id": 3,
                    "group_ids": [3],
                    "is_active_in_organization_id": 1,
                },
                "meeting/3": {
                    "name": "meeting3",
                    "committee_id": 3,
                    "group_ids": [4],
                    "is_active_in_organization_id": 1,
                },
                "meeting/4": {
                    "name": "meeting4",
                    "committee_id": 4,
                    "group_ids": [5],
                    "is_active_in_organization_id": 1,
                },
                "committee/2": {
                    "name": "com2",
                    "forward_to_committee_ids": [3, 4],
                    "meeting_ids": [1],
                },
                "committee/3": {
                    "name": "com3",
                    "meeting_ids": [2, 3],
                    "default_meeting_id": 3,
                },
                "committee/4": {
                    "name": "com4",
                    "meeting_ids": [4],
                },
                "user/3": {
                    "username": "test",
                    "is_active": True,
                    "default_password": TEST_USER_PW,
                    "password": self.auth.hash(TEST_USER_PW),
                    "meeting_user_ids": [1, 2, 3, 4],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 3,
                    "group_ids": [2],
                },
                "meeting_user/2": {
                    "meeting_id": 2,
                    "user_id": 3,
                    "group_ids": [3],
                },
                "meeting_user/3": {
                    "meeting_id": 3,
                    "user_id": 3,
                    "group_ids": [4],
                },
                "meeting_user/4": {
                    "meeting_id": 4,
                    "user_id": 3,
                    "group_ids": [5],
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
                "group/5": {
                    "meeting_id": 4,
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
                    "meetings": [
                        {
                            "id": 2,
                            "name": "meeting2",
                            "start_time": None,
                            "end_time": None,
                        },
                        {
                            "id": 3,
                            "name": "meeting3",
                            "start_time": None,
                            "end_time": None,
                        },
                    ],
                    "default_meeting_id": 3,
                },
                {
                    "id": 4,
                    "name": "com4",
                    "meetings": [
                        {
                            "id": 4,
                            "name": "meeting4",
                            "start_time": None,
                            "end_time": None,
                        }
                    ],
                    "default_meeting_id": None,
                },
            ],
        )

    def test_archived_forwarded_to_meeting(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "meeting1",
                    "committee_id": 2,
                    "is_active_in_organization_id": 1,
                },
                "meeting/2": {
                    "name": "meeting2",
                    "committee_id": 3,
                    "is_active_in_organization_id": 1,
                },
                "meeting/3": {
                    "name": "meeting3",
                    "committee_id": 3,
                    "is_active_in_organization_id": None,
                },
                "committee/2": {
                    "name": "com2",
                    "forward_to_committee_ids": [3],
                    "meeting_ids": [1],
                },
                "committee/3": {
                    "name": "com3",
                    "meeting_ids": [2, 3],
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
                    "meetings": [
                        {
                            "id": 2,
                            "name": "meeting2",
                            "start_time": None,
                            "end_time": None,
                        }
                    ],
                    "default_meeting_id": None,
                }
            ],
        )

    def test_archived_sender_meeting(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "meeting1",
                    "committee_id": 2,
                    "is_active_in_organization_id": None,
                },
                "committee/2": {
                    "name": "com2",
                    "forward_to_committee_ids": [3],
                    "meeting_ids": [1],
                },
            }
        )
        status_code, data = self.request("get_forwarding_meetings", {"meeting_id": 1})
        self.assertEqual(status_code, 400)
        self.assertEqual(
            data,
            {
                "success": False,
                "message": "Your sender meeting is an archived meeting, which can not forward motions.",
            },
        )

    def test_with_locked_meeting(self) -> None:
        self.set_models(
            {
                "meeting/3": {
                    "group_ids": [3],
                    "locked_from_inside": True,
                    "committee_id": 1,
                },
                "committee/1": {"meeting_ids": [1]},
                "group/3": {"meeting_id": 3},
            }
        )
        status_code, data = self.request("get_forwarding_meetings", {"meeting_id": 3})
        assert status_code == 403
        assert "Missing permission: motion.can_forward" in data["message"]
