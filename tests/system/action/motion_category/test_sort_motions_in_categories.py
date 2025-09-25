from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCategorySortMotionsInCategoriesActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "motion_category/222": {
                    "name": "category 222",
                    "meeting_id": 1,
                    "sequential_number": 222,
                }
            }
        )
        self.create_motion(1, 31, motion_data={"category_id": 222})

    def test_sort_correct_1(self) -> None:
        self.create_motion(1, 32, motion_data={"category_id": 222})
        response = self.request(
            "motion_category.sort_motions_in_category",
            {"id": 222, "motion_ids": [32, 31]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/31", {"category_weight": 2})
        self.assert_model_exists("motion/32", {"category_weight": 1})

    def test_sort_missing_model(self) -> None:
        response = self.request(
            "motion_category.sort_motions_in_category",
            {"id": 222, "motion_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "motion sorting failed, because element motion/32 doesn't exist.",
            response.json["message"],
        )

    def test_sort_another_section_db(self) -> None:
        self.create_motion(1, 32, motion_data={"category_id": 222})
        self.create_motion(1, 33, motion_data={"category_id": 222})
        response = self.request(
            "motion_category.sort_motions_in_category",
            {"id": 222, "motion_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "motion sorting failed, because some elements were not included in the call.",
            response.json["message"],
        )

    def test_sort_no_permission(self) -> None:
        self.create_motion(1, 32, motion_data={"category_id": 222})
        self.base_permission_test(
            {},
            "motion_category.sort_motions_in_category",
            {"id": 222, "motion_ids": [32, 31]},
        )

    def test_sort_permission(self) -> None:
        self.create_motion(1, 32, motion_data={"category_id": 222})
        self.base_permission_test(
            {},
            "motion_category.sort_motions_in_category",
            {"id": 222, "motion_ids": [32, 31]},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_sort_permission_locked_meeting(self) -> None:
        self.create_motion(1, 32, motion_data={"category_id": 222})
        self.base_locked_out_superadmin_permission_test(
            {},
            "motion_category.sort_motions_in_category",
            {"id": 222, "motion_ids": [32, 31]},
        )
