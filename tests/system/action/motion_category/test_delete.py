from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCategorySystemTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_category/111": {"name": "name_srtgb123", "meeting_id": 1}
        }

    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "test_ABC", "is_active_in_organization_id": 1},
                "motion_category/111": {"name": "name_srtgb123", "meeting_id": 222},
            }
        )
        response = self.request("motion_category.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_category/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("motion_category/112", {"name": "name_srtgb123"})
        response = self.request("motion_category.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_category/112")

    def test_delete_handle_remove_relation(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_xQyvfmsS",
                    "motion_category_ids": [111],
                    "is_active_in_organization_id": 1,
                },
                "motion/89": {"meeting_id": 222, "category_id": 111},
                "motion_category/111": {
                    "name": "name_srtgb123",
                    "prefix": "prefix_JmDHFgvH",
                    "meeting_id": 222,
                    "motion_ids": [89],
                },
            }
        )

        self.request("motion_category.delete", {"id": 111})
        motion = self.get_model("motion/89")
        assert motion.get("category_id") is None
        meeting = self.get_model("meeting/222")
        assert meeting.get("motion_category_ids") == []

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models, "motion_category.delete", {"id": 111}
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_category.delete",
            {"id": 111},
            Permissions.Motion.CAN_MANAGE,
        )
