from datetime import datetime, timedelta

from openslides_backend.models.models import Poll
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class MeetingArchiveTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def test_archive_simple(self) -> None:
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1",
            {"is_active_in_organization_id": None, "is_archived_in_organization_id": 1},
        )
        self.assert_model_exists(
            ONE_ORGANIZATION_FQID,
            {"active_meeting_ids": None, "archived_meeting_ids": [1]},
        )

    def test_archive_2_meetings(self) -> None:
        self.create_meeting(4)
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"is_active_in_organization_id": None})
        self.assert_model_exists("meeting/4", {"is_active_in_organization_id": 1})
        self.assert_model_exists(
            ONE_ORGANIZATION_FQID,
            {"active_meeting_ids": [4], "archived_meeting_ids": [1]},
        )

    def test_archive_no_permissions(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 403)
        self.assertEqual(
            "Missing permissions: Not Committee can_manage and not can_manage_organization",
            response.json["message"],
        )

    def test_archive_permission_cml(self) -> None:
        self.set_committee_management_level([60])
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"is_active_in_organization_id": None})

    def test_archive_locked_meeting(self) -> None:
        self.set_models({"meeting/1": {"locked_from_inside": True}})
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 200)

    def test_archive_permission_oml(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"is_active_in_organization_id": None})

    def test_archive_meeting_is_archived(self) -> None:
        self.update_model("meeting/1", {"is_active_in_organization_id": None})
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Meeting OpenSlides/1 cannot be changed, because it is archived.",
            response.json["message"],
        )

    def test_archive_wrong_meeting(self) -> None:
        response = self.request("meeting.archive", {"id": 2})
        self.assert_status_code(response, 400)
        self.assertEqual("Model 'meeting/2' does not exist.", response.json["message"])

    def test_archive_meeting_with_inactive_speakers(self) -> None:
        self.create_motion(1)
        now = datetime.now()
        self.set_models(
            {
                "list_of_speakers/1": {
                    "sequential_number": 1,
                    "meeting_id": 1,
                    "content_object_id": "motion/1",
                },
                "speaker/1": {
                    "list_of_speakers_id": 1,
                    "meeting_id": 1,
                    "begin_time": now - timedelta(seconds=200),
                    "end_time": now,
                },
                "speaker/2": {
                    "list_of_speakers_id": 1,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 200)

    def create_poll(self, base: int, state: str) -> None:
        self.set_models(
            {
                f"poll/{base}": {
                    "title": f"Poll {base}",
                    "type": Poll.TYPE_NAMED,
                    "backend": "fast",
                    "pollmethod": "YNA",
                    "onehundred_percent_base": "YNA",
                    "meeting_id": 1,
                    "sequential_number": base,
                    "content_object_id": "motion/1",
                    "state": state,
                }
            }
        )

    def test_archive_meeting_with_inactive_polls(self) -> None:
        self.create_motion(1)
        self.create_poll(1, Poll.STATE_CREATED)
        self.create_poll(2, Poll.STATE_FINISHED)
        self.create_poll(3, Poll.STATE_PUBLISHED)
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 200)

    def test_archive_meeting_with_active_speaker(self) -> None:
        self.create_motion(1)
        self.set_models(
            {
                "list_of_speakers/1": {
                    "sequential_number": 1,
                    "meeting_id": 1,
                    "content_object_id": "motion/1",
                },
                "speaker/1": {
                    "list_of_speakers_id": 1,
                    "meeting_id": 1,
                    "begin_time": datetime.now(),
                },
            }
        )
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertEqual(
            response.json["message"], "Cannot archive meeting with active speakers."
        )

    def test_archive_meeting_with_active_poll(self) -> None:
        self.create_motion(1)
        self.create_poll(1, Poll.STATE_STARTED)
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Cannot archive meeting with active polls.", response.json["message"]
        )

    def test_archive_meeting_with_active_speaker_and_polls(self) -> None:
        self.create_motion(1)
        self.set_models(
            {
                "list_of_speakers/1": {
                    "sequential_number": 1,
                    "meeting_id": 1,
                    "content_object_id": "motion/1",
                },
                "speaker/1": {
                    "list_of_speakers_id": 1,
                    "meeting_id": 1,
                    "begin_time": datetime.now(),
                },
            }
        )
        self.create_poll(1, Poll.STATE_STARTED)
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertEqual(
            response.json["message"],
            "Cannot archive meeting with active speakers and polls.",
        )
