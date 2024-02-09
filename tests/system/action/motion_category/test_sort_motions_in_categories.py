from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCategorySortMotionsInCategoriesActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_category/222": {
                "meeting_id": 1,
            },
            "motion/31": {"category_id": 222, "meeting_id": 1},
            "motion/32": {"category_id": 222, "meeting_id": 1},
        }

    def test_sort_correct_1(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "motion_ids": [31, 32],
                    "is_active_in_organization_id": 1,
                },
                "motion_category/222": {"meeting_id": 1},
                "motion/31": {"category_id": 222, "meeting_id": 1},
                "motion/32": {"category_id": 222, "meeting_id": 1},
            }
        )
        response = self.request(
            "motion_category.sort_motions_in_category",
            {"id": 222, "motion_ids": [32, 31]},
        )
        self.assert_status_code(response, 200)
        model_31 = self.get_model("motion/31")
        assert model_31.get("category_weight") == 2
        model_32 = self.get_model("motion/32")
        assert model_32.get("category_weight") == 1

    def test_sort_missing_model(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "motion_category/222": {"meeting_id": 1},
                "motion/31": {"category_id": 222, "meeting_id": 1},
            }
        )
        response = self.request(
            "motion_category.sort_motions_in_category",
            {"id": 222, "motion_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        assert (
            "motion sorting failed, because element motion/32 doesn't exist."
            in response.json["message"]
        )

    def test_sort_another_section_db(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "motion_category/222": {"meeting_id": 1},
                "motion/31": {"category_id": 222, "meeting_id": 1},
                "motion/32": {"category_id": 222, "meeting_id": 1},
                "motion/33": {"category_id": 222, "meeting_id": 1},
            }
        )
        response = self.request(
            "motion_category.sort_motions_in_category",
            {"id": 222, "motion_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        assert (
            "motion sorting failed, because some elements were not included in the call."
            in response.json["message"]
        )

    def test_sort_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_category.sort_motions_in_category",
            {"id": 222, "motion_ids": [32, 31]},
        )

    def test_sort_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_category.sort_motions_in_category",
            {"id": 222, "motion_ids": [32, 31]},
            Permissions.Motion.CAN_MANAGE,
        )
