from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCommentSectionSortActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_comment_section/31": {
                "meeting_id": 1,
                "name": "name_loisueb",
            },
            "motion_comment_section/32": {
                "meeting_id": 1,
                "name": "name_blanumop",
            },
        }

    def test_sort_correct_1(self) -> None:
        self.set_models(self.permission_test_models)
        response = self.request(
            "motion_comment_section.sort",
            {"meeting_id": 1, "motion_comment_section_ids": [32, 31]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_comment_section/31", {"weight": 2})
        self.assert_model_exists("motion_comment_section/32", {"weight": 1})

    def test_sort_missing_model(self) -> None:
        self.set_models(
            {
                "motion_comment_section/31": {
                    "meeting_id": 1,
                    "name": "name_loisueb",
                },
            }
        )
        response = self.request(
            "motion_comment_section.sort",
            {"meeting_id": 1, "motion_comment_section_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "motion_comment_section sorting failed, because element motion_comment_section/32 doesn't exist.",
            response.json["message"],
        )

    def test_sort_another_section_db(self) -> None:
        self.set_models(
            {
                "motion_comment_section/31": {
                    "meeting_id": 1,
                    "name": "name_loisueb",
                },
                "motion_comment_section/32": {
                    "meeting_id": 1,
                    "name": "name_blanumop",
                },
                "motion_comment_section/33": {
                    "meeting_id": 1,
                    "name": "name_polusiem",
                },
            }
        )
        response = self.request(
            "motion_comment_section.sort",
            {"meeting_id": 1, "motion_comment_section_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "motion_comment_section sorting failed, because some elements were not included in the call.",
            response.json["message"],
        )

    def test_sort_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_comment_section.sort",
            {"meeting_id": 1, "motion_comment_section_ids": [32, 31]},
        )

    def test_sort_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_comment_section.sort",
            {"meeting_id": 1, "motion_comment_section_ids": [32, 31]},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_sort_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion_comment_section.sort",
            {"meeting_id": 1, "motion_comment_section_ids": [32, 31]},
        )
