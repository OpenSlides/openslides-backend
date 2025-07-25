from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCommentCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 1},
            "motion_comment_section/78": {
                "meeting_id": 1,
                "write_group_ids": [3],
                "name": "test",
            },
        }

    def test_create(self) -> None:
        self.create_meeting(111)
        self.set_models(
            {
                "user/1": {"meeting_user_ids": [1]},
                "meeting_user/1": {
                    "meeting_id": 111,
                    "user_id": 1,
                    "group_ids": [3],
                },
                "meeting/111": {
                    "admin_group_id": 3,
                    "meeting_user_ids": [1],
                },
                "group/3": {},
                "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                "motion_comment_section/78": {"meeting_id": 111, "name": "test"},
            }
        )
        response = self.request(
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_comment/1")
        assert model.get("comment") == "test_Xcdfgee"
        assert model.get("motion_id") == 357
        assert model.get("section_id") == 78
        self.assert_history_information(
            "motion/357", ["Comment {} created", "motion_comment_section/78"]
        )

    def test_create_not_unique_error(self) -> None:
        self.create_meeting(111)
        self.set_models(
            {
                "user/1": {"meeting_user_ids": [1]},
                "meeting_user/1": {
                    "meeting_id": 111,
                    "user_id": 1,
                    "group_ids": [3],
                },
                "meeting/111": {
                    "admin_group_id": 3,
                },
                "group/3": {},
                "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                "motion_comment_section/78": {"meeting_id": 111},
                "motion_comment/4356": {
                    "comment": "test_Xcdfgee",
                    "motion_id": 357,
                    "section_id": 78,
                    "meeting_id": 111,
                },
            }
        )
        response = self.request(
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "There already exists a comment for this section, please update it instead.",
            response.json["message"],
        )

    def test_create_empty_data(self) -> None:
        response = self.request("motion_comment.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['comment', 'motion_id', 'section_id'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        self.create_meeting(111)
        self.set_models(
            {
                "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                "motion_comment_section/78": {},
            }
        )
        response = self.request(
            "motion_comment.create",
            {
                "comment": "test_Xcdfgee",
                "motion_id": 357,
                "section_id": 78,
                "wrong_field": "text_AefohteiF8",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_create_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )

    def test_create_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
            Permissions.Motion.CAN_SEE,
        )

    def test_create_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )

    def test_create_no_permission_cause_write_group(self) -> None:
        self.permission_test_models["motion_comment_section/78"]["write_group_ids"] = [
            2
        ]
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_SEE])
        self.set_models(self.permission_test_models)
        response = self.request(
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not in the write group of the section or in admin group."
            in response.json["message"]
        )

    def test_create_permission_cause_submitter(self) -> None:
        self.permission_test_models["motion_comment_section/78"]["write_group_ids"] = [
            2
        ]
        self.permission_test_models["motion_comment_section/78"][
            "submitter_can_write"
        ] = True
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_SEE])
        self.permission_test_models["motion_submitter/1234"] = {
            "meeting_user_id": 1,
            "motion_id": 357,
        }
        self.permission_test_models["meeting_user/1"] = {
            "meeting_id": 1,
            "user_id": self.user_id,
            "motion_submitter_ids": [1234],
        }
        self.set_models(self.permission_test_models)
        response = self.request(
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_comment/1",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "group_ids": [3],
                "motion_submitter_ids": [1234],
                "meeting_id": 1,
                "user_id": 2,
            },
        )

    def test_create_permission_non_meeting_committee_admin(self) -> None:
        self.set_committee_management_level([60])
        self.permission_test_models["committee/60"] = {
            "user_ids": [1],
            "manager_ids": [1],
        }
        self.base_create_permission_non_meeting_admin()

    def test_create_permission_non_meeting_orga_admin(self) -> None:
        self.base_create_permission_non_meeting_admin(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )

    def test_create_permission_non_meeting_superadmin(self) -> None:
        self.base_create_permission_non_meeting_admin(
            OrganizationManagementLevel.SUPERADMIN
        )

    def base_create_permission_non_meeting_admin(
        self, permission: OrganizationManagementLevel | None = None
    ) -> None:
        self.create_meeting()
        self.set_organization_management_level(permission)
        self.set_models(self.permission_test_models)
        response = self.request(
            "motion_comment.create",
            {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_comment/1", {"comment": "test_Xcdfgee"})
