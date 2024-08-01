from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class MeetingRevertArchivingTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "active_meeting_ids": [],
                },
                "committee/1": {
                    "name": "test_committee",
                    "organization_id": 1,
                },
                "meeting/1": {"committee_id": 1},
            }
        )

    def test_unarchive_simple(self) -> None:
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
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "active_meeting_ids": [2],
                },
            }
        )
        response = self.request("meeting.unarchive", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"is_active_in_organization_id": 1})
        organization = self.get_model(ONE_ORGANIZATION_FQID)
        self.assertCountEqual(organization["active_meeting_ids"], [1, 2])

    def test_unarchive_no_permission(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                }
            }
        )
        response = self.request("meeting.unarchive", {"id": 1})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action meeting.unarchive. Missing OrganizationManagementLevel: superadmin",
            response.json["message"],
        )

    def test_unarchive_locked_meeting(self) -> None:
        self.set_models({"meeting/1": {"locked_from_inside": True}})
        response = self.request("meeting.unarchive", {"id": 1})
        self.assert_status_code(response, 200)

    def test_unarchive_meeting_is_not_archived(self) -> None:
        self.update_model("meeting/1", {"is_active_in_organization_id": 1})
        response = self.request("meeting.unarchive", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertIn("Meeting 1 is not archived.", response.json["message"])
