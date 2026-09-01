from datetime import datetime, timedelta, tzinfo
from typing import Any
from unittest import mock
from zoneinfo import ZoneInfo

from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from .base import BasePresenterTestCase

TEST_USER_PW = "test"


class MockDateTimeMeta(type):
    def __instancecheck__(cls, instance: Any) -> bool:
        return isinstance(instance, datetime)


def mock_datetime(mocked_now: datetime) -> type[datetime]:
    class MockDateTime(datetime, metaclass=MockDateTimeMeta):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> datetime:  # type: ignore[override]
            if tz is None:
                return mocked_now
            return mocked_now.astimezone(tz)

    return MockDateTime


class TestGetForwardingMeetings(BasePresenterTestCase):
    def make_request(self, mocked_now: datetime | None = None) -> tuple[int, Any]:
        """
        Mocks the return value of datetime.now() inside of the presenter class
        to ensure correct filtering based on end_time.
        """
        if mocked_now is None:
            mocked_now = datetime.fromtimestamp(0, ZoneInfo("UTC"))

        with mock.patch(
            "openslides_backend.presenter.get_forwarding_meetings.datetime",
            mock_datetime(mocked_now),
        ):
            return super().request("get_forwarding_meetings", {"meeting_id": 1})

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
        status_code, data = self.make_request()
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

    def test_format_with_orga_time_zone(self) -> None:
        self.create_meeting()
        self.create_meeting(
            4,
            {
                "name": "meeting4",
                "start_time": datetime(2013, 3, 7, 7, 15),
                "end_time": datetime(2013, 3, 11, 19, 30),
            },
        )
        self.set_models(
            {
                "committee/60": {"forward_to_committee_ids": [63]},
                ONE_ORGANIZATION_FQID: {"time_zone": "Europe/Berlin"},
            }
        )
        status_code, data = self.make_request()
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
                            "start_time": datetime(
                                2013, 3, 7, 8, 15, tzinfo=ZoneInfo("Europe/Berlin")
                            ).isoformat(),
                            "end_time": datetime(
                                2013, 3, 11, 20, 30, tzinfo=ZoneInfo("Europe/Berlin")
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
        status_code, data = self.make_request()
        assert status_code == 403
        assert "Missing permission" in data["message"]

    def test_no_payload(self) -> None:
        status_code, data = self.request("get_forwarding_meetings")
        assert status_code == 400
        assert "No data given." == data["message"]

    def test_complex(self) -> None:
        self.create_meeting(1)
        self.create_meeting(
            4,
            {
                "name": "meeting4",
                "start_time": datetime.fromtimestamp(111111),
                "end_time": datetime.fromtimestamp(222222),
            },
        )
        self.create_meeting(
            7,
            {
                "name": "meeting7",
                "committee_id": 63,
                "start_time": datetime.fromtimestamp(333333),
                "end_time": datetime.fromtimestamp(444444),
            },
        )
        self.create_meeting(
            10,
            {
                "name": "meeting10",
                "start_time": datetime.fromtimestamp(555555),
                "end_time": datetime.fromtimestamp(666666),
            },
        )
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

        status_code, data = self.make_request()
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
                        },
                        {
                            "id": 7,
                            "name": "meeting7",
                            "start_time": datetime.fromtimestamp(
                                333333, ZoneInfo("UTC")
                            ).isoformat(),
                            "end_time": datetime.fromtimestamp(
                                444444, ZoneInfo("UTC")
                            ).isoformat(),
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
                            "start_time": datetime.fromtimestamp(
                                555555, ZoneInfo("UTC")
                            ).isoformat(),
                            "end_time": datetime.fromtimestamp(
                                666666, ZoneInfo("UTC")
                            ).isoformat(),
                        }
                    ],
                    "default_meeting_id": None,
                },
            ],
        )

    def test_archived_forwarded_to_meeting(self) -> None:
        self.create_meeting(1, {"name": "meeting1"})
        self.create_meeting(
            4,
            {
                "name": "meeting4",
                "start_time": datetime.fromtimestamp(111111),
                "end_time": datetime.fromtimestamp(222222),
            },
        )
        self.create_meeting(
            7,
            {
                "name": "meeting7",
                "committee_id": 63,
                "is_active_in_organization_id": None,
                "is_archived_in_organization_id": 1,
                "start_time": datetime.fromtimestamp(333333),
                "end_time": datetime.fromtimestamp(444444),
            },
        )
        self.set_models({"committee/60": {"forward_to_committee_ids": [63]}})
        status_code, data = self.make_request()
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
        status_code, data = self.make_request()
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
        status_code, data = self.make_request()
        assert status_code == 403
        assert "Missing permission: motion.can_forward" in data["message"]

    def test_exclude_sender_meeting(self) -> None:
        self.create_meeting(
            meeting_data={
                "start_time": datetime.fromtimestamp(111111),
                "end_time": datetime.fromtimestamp(222222),
            }
        )
        self.create_meeting(
            4,
            {
                "committee_id": 60,
                "name": "meeting4",
                "start_time": datetime.fromtimestamp(333333),
                "end_time": datetime.fromtimestamp(444444),
            },
        )
        self.create_meeting(
            7,
            {
                "start_time": datetime.fromtimestamp(555555),
                "end_time": datetime.fromtimestamp(666666),
            },
        )
        self.set_models({"committee/60": {"forward_to_committee_ids": [60, 66]}})

        status_code, data = self.make_request()
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data,
            [
                {
                    "id": 60,
                    "name": "Committee60",
                    "meetings": [
                        {
                            "id": 4,
                            "name": "meeting4",
                            "start_time": datetime.fromtimestamp(
                                333333, ZoneInfo("UTC")
                            ).isoformat(),
                            "end_time": datetime.fromtimestamp(
                                444444, ZoneInfo("UTC")
                            ).isoformat(),
                        }
                    ],
                    "default_meeting_id": None,
                },
                {
                    "id": 66,
                    "name": "Committee66",
                    "meetings": [
                        {
                            "id": 7,
                            "name": "OpenSlides",
                            "start_time": datetime.fromtimestamp(
                                555555, ZoneInfo("UTC")
                            ).isoformat(),
                            "end_time": datetime.fromtimestamp(
                                666666, ZoneInfo("UTC")
                            ).isoformat(),
                        }
                    ],
                    "default_meeting_id": None,
                },
            ],
        )

    def test_exclude_meeting_in_past(self) -> None:
        """
        Also checks that time_zone of the meeting is used for filtering
        and converting times to strings.
        """

        mocked_today_start = datetime(2012, 10, 25, tzinfo=ZoneInfo("Europe/Berlin"))
        self.create_meeting()
        self.create_meeting(
            4,
            {
                "time_zone": "Europe/Berlin",
                "name": "meeting4",
                "start_time": datetime(
                    2012, 10, 23, 9, 15, tzinfo=ZoneInfo("Europe/Berlin")
                ),
                "end_time": mocked_today_start - timedelta(microseconds=1),
            },
        )
        self.create_meeting(
            7,
            {
                "time_zone": "Europe/Berlin",
                "name": "meeting7",
                "committee_id": 63,
                "start_time": datetime(
                    2012, 10, 23, 10, 30, 14, tzinfo=ZoneInfo("Europe/Berlin")
                ),
                "end_time": mocked_today_start,
            },
        )
        self.set_models({"committee/60": {"forward_to_committee_ids": [63]}})

        status_code, data = self.make_request(
            datetime(2012, 10, 25, 10, 30, 14, tzinfo=ZoneInfo("Europe/Berlin"))
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data,
            [
                {
                    "id": 63,
                    "name": "Committee63",
                    "meetings": [
                        {
                            "id": 7,
                            "name": "meeting7",
                            "start_time": datetime(
                                2012,
                                10,
                                23,
                                10,
                                30,
                                14,
                                tzinfo=ZoneInfo("Europe/Berlin"),
                            ).isoformat(),
                            "end_time": mocked_today_start.isoformat(),
                        }
                    ],
                    "default_meeting_id": None,
                },
            ],
        )
