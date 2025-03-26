from math import floor
from time import time

from openslides_backend.models.models import Poll
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class MeetingArchiveTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "active_meeting_ids": [1],
                },
                "committee/1": {
                    "name": "test_committee",
                    "organization_id": 1,
                },
                "meeting/1": {"committee_id": 1, "is_active_in_organization_id": 1},
            }
        )

    def test_archive_simple(self) -> None:
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1",
            {"is_active_in_organization_id": None, "is_archived_in_organization_id": 1},
        )
        self.assert_model_exists(
            ONE_ORGANIZATION_FQID,
            {"active_meeting_ids": [], "archived_meeting_ids": [1]},
        )

    def test_archive_2_meetings(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "active_meeting_ids": [1, 2],
                },
            }
        )
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"is_active_in_organization_id": None})
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"active_meeting_ids": [2]})

    def test_archive_no_permissions(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
                }
            }
        )
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 403)
        self.assertIn(
            "Missing permissions: Not Committee can_manage and not can_manage_organization",
            response.json["message"],
        )

    def test_archive_permission_cml(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "committee_management_ids": [1],
                    "committee_ids": [1],
                }
            }
        )
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 200)

    def test_archive_locked_meeting(self) -> None:
        self.set_models({"meeting/1": {"locked_from_inside": True}})
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 200)

    def test_archive_permission_oml(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                }
            }
        )
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 200)

    def test_archive_meeting_is_archived(self) -> None:
        self.update_model("meeting/1", {"is_active_in_organization_id": None})
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Meeting /1 cannot be changed, because it is archived",
            response.json["message"],
        )

    def test_archive_wrong_meeting(self) -> None:
        response = self.request("meeting.archive", {"id": 2})
        self.assert_status_code(response, 400)
        self.assertIn("Model 'meeting/2' does not exist.", response.json["message"])

    def test_archive_meeting_with_inactive_speakers(self) -> None:
        now = floor(time())
        self.set_models(
            {
                "list_of_speakers/1": {
                    "meeting_id": 1,
                    "speaker_ids": [1, 2],
                },
                "speaker/1": {
                    "list_of_speakers_id": 1,
                    "meeting_id": 1,
                    "begin_time": now - 200,
                    "end_time": now - 100,
                },
                "speaker/2": {
                    "list_of_speakers_id": 1,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 200)

    def test_archive_meeting_with_inactive_polls(self) -> None:
        self.set_models(
            {
                "poll/1": {
                    "state": Poll.STATE_CREATED,
                    "meeting_id": 1,
                },
                "poll/2": {
                    "state": Poll.STATE_FINISHED,
                    "meeting_id": 1,
                },
                "poll/3": {
                    "state": Poll.STATE_PUBLISHED,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 200)

    def test_archive_meeting_with_active_speaker(self) -> None:
        self.set_models(
            {
                "list_of_speakers/1": {
                    "meeting_id": 1,
                    "speaker_ids": [1],
                },
                "speaker/1": {
                    "list_of_speakers_id": 1,
                    "meeting_id": 1,
                    "begin_time": floor(time()) - 100,
                },
            }
        )
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 400)
        assert (
            response.json["message"] == "Cannot archieve meeting with active speaker."
        )

    def test_archive_meeting_with_active_poll(self) -> None:
        self.set_models(
            {
                "poll/1": {
                    "title": "Poll 1",
                    "state": Poll.STATE_STARTED,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Cannot archieve meeting with active polls (Poll 1)."
        )

    def test_archive_meeting_with_active_speaker_and_polls(self) -> None:
        self.set_models(
            {
                "list_of_speakers/1": {
                    "meeting_id": 1,
                },
                "speaker/1": {
                    "list_of_speakers_id": 1,
                    "meeting_id": 1,
                    "begin_time": floor(time()) - 100,
                },
                "poll/1": {
                    "title": "Poll 1",
                    "state": Poll.STATE_STARTED,
                    "meeting_id": 1,
                },
                "poll/2": {
                    "title": "Poll 2",
                    "state": Poll.STATE_STARTED,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Cannot archieve meeting with active speaker and polls (Poll 1, Poll 2)."
        )
