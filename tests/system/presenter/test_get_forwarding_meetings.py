from datetime import datetime
from zoneinfo import ZoneInfo

from openslides_backend.permissions.permissions import Permissions

from .base import BasePresenterTestCase

TEST_USER_PW = "test"


class TestGetForwardingMeetings(BasePresenterTestCase):
    def test_correct(self) -> None:
        self.create_meeting(1)
        self.create_meeting(
            4,
            {
                "name": "meeting4",
                "start_time": datetime.fromtimestamp(111111),
                "end_time": datetime.fromtimestamp(222222),
            },
        )
        self.set_models({"committee/60": {"forward_to_committee_ids": [63]}})
        status_code, data = self.request("get_forwarding_meetings", {"meeting_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data,
            [
                {
                    "id": 63,
                    "name": "Committee63",
                    "meetings": [
                        {
                            "id": 4,
                            "name": "meeting4",
                            "start_time": datetime.fromtimestamp(
                                111111, ZoneInfo("UTC")
                            ).isoformat(),
                            "end_time": datetime.fromtimestamp(
                                222222, ZoneInfo("UTC")
                            ).isoformat(),
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
        self.create_meeting()
        self.set_user_groups(1, [1])
        self.set_organization_management_level(None)
        status_code, data = self.request("get_forwarding_meetings", {"meeting_id": 1})
        assert status_code == 403
        assert "Missing permission" in data["message"]

    def test_complex(self) -> None:
        self.create_meeting(1)
        self.create_meeting(4, {"name": "meeting4"})
        self.create_meeting(7, {"name": "meeting7", "committee_id": 63})
        self.create_meeting(10, {"name": "meeting10"})
        self.set_models(
            {
                "committee/60": {"forward_to_committee_ids": [63, 69]},
                "committee/63": {"default_meeting_id": 7},
            }
        )

        self.set_organization_management_level(None)
        self.set_user_groups(1, [1, 4, 7, 10])
        self.set_group_permissions(1, [Permissions.Motion.CAN_MANAGE])
        self.set_group_permissions(4, [Permissions.Motion.CAN_CREATE])

        status_code, data = self.request("get_forwarding_meetings", {"meeting_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data,
            [
                {
                    "id": 63,
                    "name": "Committee63",
                    "meetings": [
                        {
                            "id": 4,
                            "name": "meeting4",
                            "start_time": None,
                            "end_time": None,
                        },
                        {
                            "id": 7,
                            "name": "meeting7",
                            "start_time": None,
                            "end_time": None,
                        },
                    ],
                    "default_meeting_id": 7,
                },
                {
                    "id": 69,
                    "name": "Committee69",
                    "meetings": [
                        {
                            "id": 10,
                            "name": "meeting10",
                            "start_time": None,
                            "end_time": None,
                        }
                    ],
                    "default_meeting_id": None,
                },
            ],
        )

    def test_archived_forwarded_to_meeting(self) -> None:
        self.create_meeting(1, {"name": "meeting1"})
        self.create_meeting(4, {"name": "meeting4"})
        self.create_meeting(
            7,
            {
                "name": "meeting7",
                "committee_id": 63,
                "is_active_in_organization_id": None,
                "is_archived_in_organization_id": 1,
            },
        )
        self.set_models({"committee/60": {"forward_to_committee_ids": [63]}})
        status_code, data = self.request("get_forwarding_meetings", {"meeting_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data,
            [
                {
                    "id": 63,
                    "name": "Committee63",
                    "meetings": [
                        {
                            "id": 4,
                            "name": "meeting4",
                            "start_time": None,
                            "end_time": None,
                        }
                    ],
                    "default_meeting_id": None,
                }
            ],
        )

    def test_archived_sender_meeting(self) -> None:
        self.create_meeting(
            1,
            {"is_active_in_organization_id": None, "is_archived_in_organization_id": 1},
        )
        self.set_models(
            {
                "committee/60": {"forward_to_committee_ids": [63]},
                "committee/63": {"name": "Committee63"},
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
        self.create_meeting(1, {"locked_from_inside": True})
        status_code, data = self.request("get_forwarding_meetings", {"meeting_id": 1})
        assert status_code == 403
        assert "Missing permission: motion.can_forward" in data["message"]
