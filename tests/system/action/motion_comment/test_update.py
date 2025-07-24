from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCommentUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: dict[str, dict[str, Any]] = {
            "motion/111": {"meeting_id": 1, "comment_ids": [111]},
            "motion_comment/111": {
                "comment": "comment_srtgb123",
                "meeting_id": 1,
                "motion_id": 111,
                "section_id": 78,
            },
            "motion_comment_section/78": {
                "meeting_id": 1,
                "write_group_ids": [3],
                "name": "test",
            },
        }

    def test_update_correct(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/1": {"meeting_user_ids": [1]},
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [2],
                },
                "meeting/1": {"admin_group_id": 2},
                "group/2": {
                    "meeting_id": 1,
                    "admin_group_for_meeting_id": 1,
                    "meeting_user_ids": [1],
                },
                **self.test_models,
            }
        )
        response = self.request(
            "motion_comment.update", {"id": 111, "comment": "comment_Xcdfgee"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_comment/111")
        assert model.get("comment") == "comment_Xcdfgee"
        self.assert_history_information(
            "motion/111", ["Comment {} updated", "motion_comment_section/78"]
        )

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "motion_comment/111": {
                    "comment": "comment_srtgb123",
                    "meeting_id": 1,
                    "section_id": 78,
                },
                "motion_comment_section/78": {"meeting_id": 1, "write_group_ids": [3]},
            }
        )
        response = self.request(
            "motion_comment.update", {"id": 112, "comment": "comment_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_comment/111")
        assert model.get("comment") == "comment_srtgb123"

    def test_update_no_permission(self) -> None:
        self.base_permission_test(
            self.test_models,
            "motion_comment.update",
            {"id": 111, "comment": "comment_Xcdfgee"},
        )

    def test_update_permission(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_SEE])
        self.set_models(self.test_models)
        response = self.request(
            "motion_comment.update",
            {"comment": "test_Xcdfgee", "id": 111},
        )
        self.assert_status_code(response, 200)

    def test_update_permissions_locked_meeting(self) -> None:
        self.create_meeting()
        self.set_models(self.test_models)
        self.base_locked_out_superadmin_permission_test(
            self.test_models,
            "motion_comment.update",
            {"id": 111, "comment": "comment_Xcdfgee"},
        )

    def test_update_no_permission_cause_write_group(self) -> None:
        self.test_models["motion_comment_section/78"]["write_group_ids"] = [2]
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_SEE])
        self.set_models(self.test_models)
        response = self.request(
            "motion_comment.update",
            {"comment": "test_Xcdfgee", "id": 111},
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not in the write group of the section or in admin group."
            in response.json["message"]
        )

    def test_update_permission_in_admin_group(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.set_user_groups(self.user_id, [2])
        self.login(self.user_id)
        self.set_models(self.test_models)
        response = self.request(
            "motion_comment.update",
            {"comment": "test_Xcdfgee", "id": 111},
        )
        self.assert_status_code(response, 200)

    def test_update_permission_cause_submitter(self) -> None:
        self.test_models["motion_comment_section/78"]["write_group_ids"] = [2]
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_SEE])
        self.test_models["motion_comment_section/78"]["submitter_can_write"] = True
        self.test_models["motion_submitter/777"] = {
            "meeting_user_id": 1,
            "motion_id": 111,
        }
        self.test_models["motion/111"]["submitter_ids"] = [self.user_id]
        self.test_models["meeting_user/1"] = {
            "meeting_id": 1,
            "user_id": self.user_id,
            "motion_submitter_ids": [777],
        }
        self.set_models(self.test_models)
        response = self.request(
            "motion_comment.update",
            {"comment": "test_Xcdfgee", "id": 111},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_comment/111", {"comment": "test_Xcdfgee"})

    def test_update_permission_non_meeting_committee_admin(self) -> None:
        self.set_committee_management_level([60])
        self.test_models["committee/60"] = {"user_ids": [1], "manager_ids": [1]}
        self.base_update_permission_non_meeting_admin()

    def test_update_permission_non_meeting_orga_admin(self) -> None:
        self.base_update_permission_non_meeting_admin(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )

    def test_update_permission_non_meeting_superadmin(self) -> None:
        self.base_update_permission_non_meeting_admin(
            OrganizationManagementLevel.SUPERADMIN
        )

    def base_update_permission_non_meeting_admin(
        self, permission: OrganizationManagementLevel | None = None
    ) -> None:
        self.create_meeting()
        self.set_organization_management_level(permission)
        self.set_models(self.test_models)
        response = self.request(
            "motion_comment.update",
            {"comment": "test_Xcdfgee", "id": 111},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_comment/111", {"comment": "test_Xcdfgee"})
