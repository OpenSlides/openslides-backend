from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCategorySystemTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion/89": {
                "title": "motion 89",
                "meeting_id": 1,
                "state_id": 1,
                "sequential_number": 89,
            },
            "motion_category/111": {
                "name": "name_srtgb123",
                "prefix": "prefix_JmDHFgvH",
                "meeting_id": 1,
                "sequential_number": 111,
            },
        }

    def test_update_correct_all_fields(self) -> None:
        self.set_models(self.permission_test_models)
        response = self.request(
            "motion_category.update",
            {
                "id": 111,
                "name": "name_Xcdfgee",
                "prefix": "prefix_sthyAKrW",
                "motion_ids": [89],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_category/111",
            {"name": "name_Xcdfgee", "prefix": "prefix_sthyAKrW", "motion_ids": [89]},
        )

    def test_update_delete_prefix(self) -> None:
        self.set_models(
            {
                "motion_category/111": {
                    "name": "name_srtgb123",
                    "prefix": "prefix_JmDHFgvH",
                    "meeting_id": 1,
                    "sequential_number": 111,
                }
            }
        )
        response = self.request("motion_category.update", {"id": 111, "prefix": None})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_category/111", {"prefix": None})

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "motion_category/111": {
                    "name": "name_srtgb123",
                    "prefix": "prefix_JmDHFgvH",
                    "meeting_id": 1,
                    "sequential_number": 111,
                }
            }
        )
        response = self.request(
            "motion_category.update", {"id": 112, "name": "name_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_category/111", {"name": "name_srtgb123"})

    def test_update_non_unique_prefix(self) -> None:
        self.set_models(
            {
                "motion_category/111": {
                    "name": "name_srtgb123",
                    "prefix": "bla",
                    "meeting_id": 1,
                    "sequential_number": 111,
                },
                "motion_category/110": {
                    "name": "name_already",
                    "prefix": "test",
                    "meeting_id": 1,
                    "sequential_number": 110,
                },
            }
        )
        response = self.request("motion_category.update", {"id": 111, "prefix": "test"})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_category/111",
            {
                "name": "name_srtgb123",
                "prefix": "test",
                "meeting_id": 1,
            },
        )

    def test_update_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_category.update",
            {"id": 111, "name": "name_Xcdfgee"},
        )

    def test_update_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_category.update",
            {"id": 111, "name": "name_Xcdfgee"},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_update_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion_category.update",
            {"id": 111, "name": "name_Xcdfgee"},
        )
