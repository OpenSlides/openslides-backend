from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCategoryNumberMotionsTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_category/111": {
                "name": "name_MKKAcYQu",
                "prefix": "prefix_A",
                "meeting_id": 1,
                "sequential_number": 111,
            },
            "motion/69": {
                "title": "title_NAZOknoM",
                "category_id": 111,
                "meeting_id": 1,
                "state_id": 1,
                "sequential_number": 69,
            },
        }

    def test_good_single_motion(self) -> None:
        check_time = datetime.now(ZoneInfo("UTC"))
        self.set_models(self.permission_test_models)

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
                },
                "motion/78": {
                    "title": "title_NAZOknoM",
                    "category_id": 78,
                    "meeting_id": 1,
                    "state_id": 1,
                    "sequential_number": 78,
                },
                "motion/85": {
                    "title": "title_MyMayxxr",
                    "category_id": 78,
                    "meeting_id": 1,
                    "state_id": 1,
                    "sequential_number": 85,
                },
                "motion_category/111": {
                    "name": "name_MKKAcYQu",
                    "prefix": "prefix_A",
                    "meeting_id": 1,
                    "sequential_number": 111,
                },
                "motion_category/78": {
                    "name": "name_xSBwbHAT",
                    "parent_id": 111,
                    "meeting_id": 1,
                    "sequential_number": 78,
                },
                "motion_category/114": {
                    "name": "name_pIObKJwT",
                    "parent_id": 111,
                    "prefix": "prefix_C",
                    "meeting_id": 1,
                    "sequential_number": 114,
                },
            }
        )
        response = self.request("motion_category.number_motions", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/78", {"number": "prefix_A 001"})
        self.assert_model_exists("motion/85", {"number": "prefix_A 002"})

    def test_check_amendments_error_case(self) -> None:
        self.set_models(
            {
                "motion/78": {
                    "title": "title_NAZOknoM",
                    "meeting_id": 1,
                    "state_id": 1,
                    "category_id": 78,
                    "sequential_number": 78,
                },
                "motion/666": {
                    "title": "title_XtzUEFdl",
                    "meeting_id": 1,
                    "state_id": 1,
                    "sequential_number": 666,
                },
                "motion/85": {
                    "title": "title_MyMayxxr",
                    "lead_motion_id": 666,
                    "meeting_id": 1,
                    "state_id": 1,
                    "category_id": 78,
                    "sequential_number": 85,
                },
                "motion_category/111": {
                    "name": "name_MKKAcYQu",
                    "meeting_id": 1,
                    "sequential_number": 111,
                },
                "motion_category/78": {
                    "name": "name_xSBwbHAT",
                    "parent_id": 111,
                    "meeting_id": 1,
                    "sequential_number": 78,
                },
                "motion_category/114": {
                    "name": "name_pIObKJwT",
                    "parent_id": 111,
                    "meeting_id": 1,
                    "sequential_number": 114,
                },
            }
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
                "motion_category/1": {
                    "name": "name_category_1",
                    "meeting_id": 1,
                    "sequential_number": 1,
                },
                "motion_category/2": {
                    "name": "name_category_2",
                    "parent_id": 1,
                    "prefix": "A",
                    "meeting_id": 1,
                    "sequential_number": 2,
                },
                "motion_category/3": {
                    "name": "name_category_3",
                    "parent_id": 1,
                    "prefix": "B",
                    "meeting_id": 1,
                    "sequential_number": 13,
                },
                "motion/1": {
                    "title": "title_motion_1",
                    "category_id": 2,
                    "meeting_id": 1,
                    "state_id": 1,
                    "sequential_number": 1,
                },
                "motion/2": {
                    "title": "title_motion_2",
                    "category_id": 2,
                    "meeting_id": 1,
                    "state_id": 1,
                    "sequential_number": 2,
                },
                "motion/3": {
                    "title": "title_motion_3",
                    "category_id": 3,
                    "meeting_id": 1,
                    "state_id": 1,
                    "sequential_number": 3,
                },
                "motion/4": {
                    "title": "title_motion_4",
                    "category_id": 3,
                    "meeting_id": 1,
                    "lead_motion_id": 3,
                    "state_id": 1,
                    "sequential_number": 4,
                },
                "motion/5": {
                    "title": "title_motion_5",
                    "category_id": 3,
                    "meeting_id": 1,
                    "lead_motion_id": 3,
                    "state_id": 1,
                    "sequential_number": 5,
                },
            }
        )

        response = self.request("motion_category.number_motions", {"id": 1})
        self.assert_status_code(response, 200)

        self.assert_model_exists("motion/1", {"number": "A 001"})
        self.assert_model_exists("motion/2", {"number": "A 002"})
        self.assert_model_exists("motion/3", {"number": "B 003"})
        self.assert_model_exists("motion/4", {"number": "B 003 X 001"})
        self.assert_model_exists("motion/5", {"number": "B 003 X 002"})

    def test_already_existing_number(self) -> None:
        self.set_models(self.permission_test_models)
        self.set_models(
            {
                "motion/70": {
                    "title": "title_NAZOknoM",
                    "meeting_id": 1,
                    "number": "prefix_A01",
                    "state_id": 1,
                    "sequential_number": 70,
                },
            }
        )
        response = self.request("motion_category.number_motions", {"id": 111})
        self.assert_status_code(response, 400)
        self.assertEqual(
            'Numbering aborted because the motion identifier "prefix_A01" already exists.',
            response.json["message"],
        )

    def test_sort_categories(self) -> None:
        self.set_models(
            {
                "motion_category/1": {
                    "name": "category_1",
                    "meeting_id": 1,
                    "sequential_number": 1,
                },
                "motion_category/2": {
                    "name": "category_2",
                    "meeting_id": 1,
                    "parent_id": 1,
                    "prefix": "C",
                    "weight": 100,
                    "sequential_number": 2,
                },
                "motion_category/3": {
                    "name": "category_3",
                    "meeting_id": 1,
                    "parent_id": 1,
                    "prefix": "A",
                    "weight": 1,
                    "sequential_number": 3,
                },
                "motion_category/4": {
                    "name": "category_4",
                    "meeting_id": 1,
                    "parent_id": 1,
                    "prefix": "B",
                    "weight": 10,
                    "sequential_number": 4,
                },
                "motion/1": {
                    "title": "m1",
                    "category_id": 2,
                    "meeting_id": 1,
                    "state_id": 1,
                    "category_weight": 100,
                    "sequential_number": 1,
                },
                "motion/2": {
                    "title": "m2",
                    "category_id": 3,
                    "meeting_id": 1,
                    "state_id": 1,
                    "category_weight": 10,
                    "sequential_number": 2,
                },
                "motion/3": {
                    "title": "m3",
                    "category_id": 4,
                    "meeting_id": 1,
                    "state_id": 1,
                    "category_weight": 1,
                    "sequential_number": 3,
                },
            }
        )
        response = self.request("motion_category.number_motions", {"id": 1})
        self.assert_status_code(response, 200)

        self.assert_model_exists("motion/1", {"number": "C03"})
        self.assert_model_exists("motion/2", {"number": "A01"})
        self.assert_model_exists("motion/3", {"number": "B02"})

    def test_sort_motions(self) -> None:
        self.set_models(
            {
                "motion_category/1": {
                    "name": "category_1",
                    "meeting_id": 1,
                    "sequential_number": 1,
                },
                "motion/1": {
                    "title": "m1",
                    "category_id": 1,
                    "meeting_id": 1,
                    "state_id": 1,
                    "category_weight": 100,
                    "sequential_number": 1,
                },
                "motion/2": {
                    "title": "m2",
                    "category_id": 1,
                    "meeting_id": 1,
                    "state_id": 1,
                    "category_weight": 10,
                    "sequential_number": 2,
                },
                "motion/3": {
                    "title": "m3",
                    "category_id": 1,
                    "meeting_id": 1,
                    "state_id": 1,
                    "category_weight": 1,
                    "sequential_number": 3,
                },
            }
        )
        response = self.request("motion_category.number_motions", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"number": "03"})
        self.assert_model_exists("motion/2", {"number": "02"})
        self.assert_model_exists("motion/3", {"number": "01"})

    def test_stop_prefix_lookup_at_main_category(self) -> None:
        self.set_models(
            {
                "motion_category/1": {
                    "name": "category_1",
                    "meeting_id": 1,
                    "prefix": "A",
                    "sequential_number": 1,
                },
                "motion_category/2": {
                    "name": "category_2",
                    "meeting_id": 1,
                    "parent_id": 1,
                    "sequential_number": 2,
                },
                "motion/1": {
                    "title": "m1",
                    "category_id": 2,
                    "meeting_id": 1,
                    "state_id": 1,
                    "category_weight": 100,
                    "sequential_number": 1,
                },
            }
        )

        response = self.request("motion_category.number_motions", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"number": "01"})

    def test_invalid_id(self) -> None:
        self.set_models(
            {
                "motion_category/1": {
                    "name": "category_1",
                    "meeting_id": 1,
                    "prefix": "A",
                    "sequential_number": 1,
                },
                "motion_category/2": {
                    "name": "category_2",
                    "meeting_id": 1,
                    "parent_id": 1,
                    "sequential_number": 2,
                },
                "motion/1": {
                    "title": "m1",
                    "category_id": 2,
                    "meeting_id": 1,
                    "state_id": 1,
                    "category_weight": 100,
                    "sequential_number": 1,
                },
            }
        )

        response = self.request("motion_category.number_motions", {"id": 222})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Model 'motion_category/222' does not exist.", response.json["message"]
        )

    def test_number_motions_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models, "motion_category.number_motions", {"id": 111}
        )

    def test_number_motions_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_category.number_motions",
            {"id": 111},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_number_motions_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models, "motion_category.number_motions", {"id": 111}
        )
