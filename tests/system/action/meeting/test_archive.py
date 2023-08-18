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

    def test_archive_with_users(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "committee_ids": [1],
                    "active_meeting_ids": [1, 2],
                    "archived_meeting_ids": [],
                    "user_ids": [1, 2, 3, 4, 5],
                },
                "committee/1": {
                    "name": "test_committee",
                    "organization_id": 1,
                    "meeting_ids": [1, 2],
                    "default_meeting_id": 1,
                    "user_ids": [1, 2, 3, 4, 5],
                    "manager_ids": [3, 5],
                },
                "meeting/1": {
                    "name": "to archive",
                    "user_ids": [2, 4, 5],
                    "group_ids": [1],
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "default_meeting_for_committee_id": 1,
                    "meeting_user_ids": [12, 14, 15],
                },
                "meeting/2": {
                    "name": "m1",
                    "user_ids": [4],
                    "group_ids": [2],
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [24],
                },
                "group/1": {
                    "meeting_user_ids": [12, 14, 15],
                    "meeting_id": 1,
                    "name": "g1",
                },
                "group/2": {"meeting_user_ids": [24], "meeting_id": 2, "name": "g2"},
                "user/2": {
                    "username": "only in meeting to archive",
                    "meeting_ids": [1],
                    "meeting_user_ids": [12],
                    "committee_ids": [1],
                    "organization_id": 1,
                    "is_active": True,
                },
                "user/3": {
                    "username": "only committee manager",
                    "meeting_ids": [],
                    "meeting_user_ids": [],
                    "committee_management_ids": [1],
                    "committee_ids": [1],
                    "organization_id": 1,
                    "is_active": True,
                },
                "user/4": {
                    "username": "both meetings",
                    "meeting_ids": [1, 2],
                    "meeting_user_ids": [14, 24],
                    "committee_ids": [1],
                    "organization_id": 1,
                    "is_active": True,
                },
                "user/5": {
                    "username": "meeting to archive and committee",
                    "meeting_ids": [1],
                    "meeting_user_ids": [15],
                    "committee_management_ids": [1],
                    "committee_ids": [1],
                    "organization_id": 1,
                    "is_active": True,
                },
                "meeting_user/12": {
                    "user_id": 2,
                    "meeting_id": 1,
                    "group_ids": [1],
                },
                "meeting_user/14": {
                    "user_id": 4,
                    "meeting_id": 1,
                    "group_ids": [1],
                },
                "meeting_user/24": {
                    "user_id": 4,
                    "meeting_id": 2,
                    "group_ids": [2],
                },
                "meeting_user/15": {
                    "user_id": 5,
                    "meeting_id": 1,
                    "group_ids": [1],
                },
            }
        )

        response = self.request("meeting.archive", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            ONE_ORGANIZATION_FQID,
            {
                "user_ids": [1, 2, 3, 4, 5],
                "archived_meeting_ids": [1],
                "active_meeting_ids": [2],
            },
        )
        self.assert_model_exists(
            "committee/1",
            {
                "user_ids": [1, 2, 3, 4, 5],
                "meeting_ids": [1, 2],
                "manager_ids": [3, 5],
            },
        )
        self.assert_model_exists(
            "meeting/1",
            {
                "user_ids": [2, 4, 5],
                "default_meeting_for_committee_id": 1,
                "is_active_in_organization_id": None,
                "is_archived_in_organization_id": 1,
            },
        )
        self.assert_model_exists(
            "group/1", {"meeting_user_ids": [12, 14, 15], "meeting_id": 1}
        )
        self.assert_model_exists("group/2", {"meeting_user_ids": [24], "meeting_id": 2})
        self.assert_model_exists(
            "user/2",
            {
                "username": "only in meeting to archive",
                "is_active": True,
                "meeting_ids": [1],
                "meeting_user_ids": [12],
                "committee_ids": [1],
                "organization_id": 1,
            },
        )
        self.assert_model_exists(
            "user/3",
            {
                "username": "only committee manager",
                "meeting_ids": [],
                "committee_management_ids": [1],
                "committee_ids": [1],
                "organization_id": 1,
                "is_active": True,
            },
        )
        self.assert_model_exists(
            "user/4",
            {
                "username": "both meetings",
                "meeting_ids": [1, 2],
                "meeting_user_ids": [14, 24],
                "committee_ids": [1],
                "organization_id": 1,
                "is_active": True,
            },
        )
        self.assert_model_exists(
            "user/5",
            {
                "username": "meeting to archive and committee",
                "meeting_ids": [1],
                "meeting_user_ids": [15],
                "committee_management_ids": [1],
                "committee_ids": [1],
                "organization_id": 1,
                "is_active": True,
            },
        )
        self.assert_model_exists(
            "meeting_user/12", {"user_id": 2, "meeting_id": 1, "group_ids": [1]}
        )
        self.assert_model_exists(
            "meeting_user/14", {"user_id": 4, "meeting_id": 1, "group_ids": [1]}
        )
        self.assert_model_exists(
            "meeting_user/24", {"user_id": 4, "meeting_id": 2, "group_ids": [2]}
        )
        self.assert_model_exists(
            "meeting_user/15", {"user_id": 5, "meeting_id": 1, "group_ids": [1]}
        )

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
