from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.typing import PartialModel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class MeetingRevertArchivingTest(BaseActionTestCase):
    def create_archived_meeting(self, meeting_data: PartialModel = {}) -> None:
        self.create_meeting(
            meeting_data={"is_active_in_organization_id": None, **meeting_data}
        )

    def test_unarchive_simple(self) -> None:
        self.create_archived_meeting()
        response = self.request("meeting.unarchive", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1",
            {"is_active_in_organization_id": 1, "is_archived_in_organization_id": None},
        )
        self.assert_model_exists(
            ONE_ORGANIZATION_FQID,
            {"active_meeting_ids": [1], "archived_meeting_ids": None},
        )

    def test_unarchive_2_meetings(self) -> None:
        self.create_archived_meeting()
        self.create_meeting(4)
        response = self.request("meeting.unarchive", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"is_active_in_organization_id": 1})
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"active_meeting_ids": [1, 4]})

    def test_unarchive_no_permission(self) -> None:
        self.create_archived_meeting()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        response = self.request("meeting.unarchive", {"id": 1})
        self.assert_status_code(response, 403)
        self.assertEqual(
            "You are not allowed to perform action meeting.unarchive. Missing OrganizationManagementLevel: superadmin",
            response.json["message"],
        )

    def test_unarchive_locked_meeting(self) -> None:
        self.create_archived_meeting({"locked_from_inside": True})
        response = self.request("meeting.unarchive", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"is_active_in_organization_id": 1})

    def test_unarchive_meeting_is_not_archived(self) -> None:
        self.create_meeting()
        response = self.request("meeting.unarchive", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertEqual("Meeting 1 is not archived.", response.json["message"])
