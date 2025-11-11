from datetime import datetime
from zoneinfo import ZoneInfo

from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.typing import PartialModel
from tests.system.action.base import BaseActionTestCase


class MotionCategoryNumberMotionsTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def create_motion_category(
        self, meeting_id: int = 1, base: int = 111, category_data: PartialModel = {}
    ) -> None:
        self.set_models(
            {
                f"motion_category/{base}": {
                    "name": f"category {base}",
                    "meeting_id": meeting_id,
                    **category_data,
                }
            }
        )

    def test_good_single_motion(self) -> None:
        check_time = datetime.now(ZoneInfo("UTC"))
        self.create_motion_category(1, 111, {"prefix": "prefix_A"})
        self.create_motion(1, 69, motion_data={"category_id": 111})

        response = self.request("motion_category.number_motions", {"id": 111})
        self.assert_status_code(response, 200)
        model = self.assert_model_exists("motion/69", {"number": "prefix_A01"})
        assert (
            model.get("last_modified", datetime.fromtimestamp(0, ZoneInfo("UTC")))
            >= check_time
        )
        self.assert_history_information("motion/69", ["Number set"])

    def test_two_motions(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "motions_number_with_blank": True,
                    "motions_number_min_digits": 3,
                }
            }
        )
        self.create_motion_category(1, 111, {"prefix": "prefix_A"})
        self.create_motion_category(1, 78, {"parent_id": 111})
        self.create_motion(1, 78, motion_data={"category_id": 78})
        self.create_motion(1, 85, motion_data={"category_id": 78})

        response = self.request("motion_category.number_motions", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/78", {"number": "prefix_A 001"})
        self.assert_model_exists("motion/85", {"number": "prefix_A 002"})

    def test_check_amendments_error_case(self) -> None:
        self.create_motion_category(1, 111)
        self.create_motion_category(1, 78, {"parent_id": 111})
        self.create_motion_category(1, 114, {"parent_id": 111})

        self.create_motion(1, 78, motion_data={"category_id": 78})
        self.create_motion(1, 666)
        self.create_motion(
            1, 85, motion_data={"lead_motion_id": 666, "category_id": 78}
        )

        response = self.request("motion_category.number_motions", {"id": 111})
        self.assert_status_code(response, 400)
        self.assertEqual(
            'Amendment "85" cannot be numbered, because it\'s lead motion (666) is not in category 111 or any subcategory.',
            response.json["message"],
        )

    def test_3_categories_5_motions_some_with_lead_motion_ids(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "motions_number_with_blank": True,
                    "motions_number_min_digits": 3,
                    "motions_amendments_prefix": "X",
                },
            }
        )
        self.create_motion_category(1, 1)
        self.create_motion_category(1, 2, {"parent_id": 1, "prefix": "A"})
        self.create_motion_category(1, 3, {"parent_id": 1, "prefix": "B"})

        self.create_motion(1, 1, motion_data={"category_id": 2})
        self.create_motion(1, 2, motion_data={"category_id": 2})
        self.create_motion(1, 3, motion_data={"category_id": 3})
        self.create_motion(1, 4, motion_data={"category_id": 3, "lead_motion_id": 3})
        self.create_motion(1, 5, motion_data={"category_id": 3, "lead_motion_id": 3})

        response = self.request("motion_category.number_motions", {"id": 1})
        self.assert_status_code(response, 200)

        self.assert_model_exists("motion/1", {"number": "A 001"})
        self.assert_model_exists("motion/2", {"number": "A 002"})
        self.assert_model_exists("motion/3", {"number": "B 003"})
        self.assert_model_exists("motion/4", {"number": "B 003 X 001"})
        self.assert_model_exists("motion/5", {"number": "B 003 X 002"})

    def test_already_existing_number(self) -> None:
        self.create_motion_category(1, 111, {"prefix": "prefix_A"})
        self.create_motion(
            1, 69, motion_data={"category_id": 111, "number": "prefix_A01"}
        )
        self.create_motion(1, 70, motion_data={"number": "prefix_A01"})
        response = self.request("motion_category.number_motions", {"id": 111})
        self.assert_status_code(response, 400)
        self.assertEqual(
            'Numbering aborted because the motion identifier "prefix_A01" already exists.',
            response.json["message"],
        )

    def test_sort_categories(self) -> None:
        self.create_motion_category(1, 1)
        self.create_motion_category(
            1, 2, {"parent_id": 1, "prefix": "C", "weight": 100}
        )
        self.create_motion_category(1, 3, {"parent_id": 1, "prefix": "A", "weight": 1})
        self.create_motion_category(1, 4, {"parent_id": 1, "prefix": "B", "weight": 10})

        self.create_motion(1, 1, motion_data={"category_id": 2, "category_weight": 100})
        self.create_motion(1, 2, motion_data={"category_id": 3, "category_weight": 10})
        self.create_motion(1, 3, motion_data={"category_id": 4, "category_weight": 1})

        response = self.request("motion_category.number_motions", {"id": 1})
        self.assert_status_code(response, 200)

        self.assert_model_exists("motion/1", {"number": "C03"})
        self.assert_model_exists("motion/2", {"number": "A01"})
        self.assert_model_exists("motion/3", {"number": "B02"})

    def test_sort_motions(self) -> None:
        self.create_motion_category(1, 1)
        self.create_motion(1, 1, motion_data={"category_id": 1, "category_weight": 100})
        self.create_motion(1, 2, motion_data={"category_id": 1, "category_weight": 10})
        self.create_motion(1, 3, motion_data={"category_id": 1, "category_weight": 1})

        response = self.request("motion_category.number_motions", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"number": "03"})
        self.assert_model_exists("motion/2", {"number": "02"})
        self.assert_model_exists("motion/3", {"number": "01"})

    def test_stop_prefix_lookup_at_main_category(self) -> None:
        self.create_motion_category(1, 1, {"prefix": "A"})
        self.create_motion_category(1, 2, {"parent_id": 1})
        self.create_motion(1, 1, motion_data={"category_id": 2, "category_weight": 100})

        response = self.request("motion_category.number_motions", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"number": "01"})

    def test_invalid_id(self) -> None:
        self.create_motion_category()
        self.create_motion(1, 1, motion_data={"category_id": 111})

        response = self.request("motion_category.number_motions", {"id": 222})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Model 'motion_category/222' does not exist.", response.json["message"]
        )

    def test_number_motions_no_permissions(self) -> None:
        self.create_motion_category()
        self.base_permission_test({}, "motion_category.number_motions", {"id": 111})

    def test_number_motions_permissions(self) -> None:
        self.create_motion_category()
        self.base_permission_test(
            {},
            "motion_category.number_motions",
            {"id": 111},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_number_motions_permissions_locked_meeting(self) -> None:
        self.create_motion_category()
        self.base_locked_out_superadmin_permission_test(
            {}, "motion_category.number_motions", {"id": 111}
        )
