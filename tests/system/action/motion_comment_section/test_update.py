from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCommentSectionActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_comment_section/111": {
                "name": "name_srtgb123",
                "meeting_id": 1,
            },
            "group/23": {"meeting_id": 1, "name": "name_asdfetza"},
        }

    def test_update_correct_all_fields(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_xQyvfmsS",
                    "is_active_in_organization_id": 1,
                },
                "motion_comment_section/111": {
                    "name": "name_srtgb123",
                    "meeting_id": 222,
                },
                "group/23": {"meeting_id": 222, "name": "name_asdfetza"},
            }
        )
        response = self.request(
            "motion_comment_section.update",
            {
                "id": 111,
                "name": "name_iuqAPRuD",
                "read_group_ids": [23],
                "write_group_ids": [23],
                "submitter_can_write": False,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_comment_section/111")
        assert model.get("name") == "name_iuqAPRuD"
        assert model.get("meeting_id") == 222
        assert model.get("read_group_ids") == [23]
        assert model.get("write_group_ids") == [23]
        assert model.get("submitter_can_write") is False

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_xQyvfmsS",
                    "is_active_in_organization_id": 1,
                },
                "group/23": {"meeting_id": 222, "name": "name_asdfetza"},
                "group/24": {"meeting_id": 222, "name": "name_faofetza"},
                "motion_comment_section/111": {
                    "name": "name_srtgb123",
                    "meeting_id": 222,
                    "read_group_ids": [23],
                },
            }
        )
        response = self.request(
            "motion_comment_section.update", {"id": 112, "read_group_ids": [24]}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_comment_section/111")
        assert model.get("read_group_ids") == [23]

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_comment_section.update",
            {
                "id": 111,
                "name": "name_iuqAPRuD",
                "read_group_ids": [23],
                "write_group_ids": [23],
            },
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_comment_section.update",
            {
                "id": 111,
                "name": "name_iuqAPRuD",
                "read_group_ids": [23],
                "write_group_ids": [23],
            },
            Permissions.Motion.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion_comment_section.update",
            {
                "id": 111,
                "name": "name_iuqAPRuD",
                "read_group_ids": [23],
                "write_group_ids": [23],
            },
        )

    def test_update_anonymous_may_read(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {"motion_comment_section_ids": [111]},
                "motion_comment_section/111": {
                    "name": "name_srtgb123",
                    "meeting_id": 1,
                },
            }
        )
        anonymous_group = self.set_anonymous()
        response = self.request(
            "motion_comment_section.update",
            {
                "id": 111,
                "read_group_ids": [anonymous_group],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_comment_section/111",
            {
                "read_group_ids": [anonymous_group],
            },
        )

    def test_update_anonymous_may_not_write(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {"motion_comment_section_ids": [111]},
                "motion_comment_section/111": {
                    "name": "name_srtgb123",
                    "meeting_id": 1,
                },
            }
        )
        anonymous_group = self.set_anonymous()
        response = self.request(
            "motion_comment_section.update",
            {
                "id": 111,
                "write_group_ids": [anonymous_group],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Anonymous group is not allowed in write_group_ids.",
            response.json["message"],
        )
