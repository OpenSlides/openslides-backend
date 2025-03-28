from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCommentSectionActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(22)
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_comment_section/111": {
                "name": "name_srtgb123",
                "meeting_id": 1,
            },
        }

    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "motion_comment_section/111": {
                    "name": "name_srtgb123",
                    "meeting_id": 22,
                },
            }
        )
        response = self.request("motion_comment_section.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_comment_section/111")

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "motion_comment_section/112": {
                    "name": "name_srtgb123",
                    "meeting_id": 22,
                },
            }
        )
        response = self.request("motion_comment_section.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_comment_section/112")

    def test_delete_existing_comments(self) -> None:
        self.set_models(
            {
                "motion_comment/79": {"motion_id": 17, "meeting_id": 22},
                "motion_comment_section/1141": {"comment_ids": [79], "meeting_id": 22},
            }
        )

        response = self.request("motion_comment_section.delete", {"id": 1141})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_comment_section/1141")
        assert (
            'This section has still comments in motion "17". Please remove all comments before deletion.'
            in response.json["message"]
        )

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_comment_section.delete",
            {"id": 111},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_comment_section.delete",
            {"id": 111},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion_comment_section.delete",
            {"id": 111},
        )
