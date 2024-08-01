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
