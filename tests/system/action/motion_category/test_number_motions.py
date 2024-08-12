import time
from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCategoryNumberMotionsTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "name": "meeting_1",
                "motion_category_ids": [111],
                "motion_ids": [69],
                "is_active_in_organization_id": 1,
            },
            "motion_category/111": {
                "name": "name_MKKAcYQu",
                "prefix": "prefix_A",
                "motion_ids": [69],
                "meeting_id": 1,
            },
            "motion/69": {
                "title": "title_NAZOknoM",
                "category_id": 111,
                "meeting_id": 1,
            },
        }

    def test_good_single_motion(self) -> None:
        check_time = round(time.time())
        self.set_models(self.permission_test_models)
        response = self.request(
            "motion_category.number_motions",
            {
                "id": 111,
            },
        )
        self.assert_status_code(response, 200)
        motion_69 = self.get_model("motion/69")
        assert motion_69.get("number") == "prefix_A1"
        assert motion_69.get("last_modified", 0) >= check_time
        self.assert_history_information("motion/69", ["Number set"])

    def test_two_motions(self) -> None:
        self.set_models(
            {
                "meeting/35": {
                    "name": "name_meeting35",
                    "motions_number_with_blank": True,
                    "motions_number_min_digits": 3,
                    "motion_ids": [78, 85],
                    "motion_category_ids": [111, 78, 114],
                    "is_active_in_organization_id": 1,
                },
                "motion/78": {
                    "title": "title_NAZOknoM",
                    "category_id": 78,
                    "meeting_id": 35,
                },
                "motion/85": {
                    "title": "title_MyMayxxr",
                    "category_id": 78,
                    "meeting_id": 35,
                },
                "motion_category/111": {
                    "name": "name_MKKAcYQu",
                    "child_ids": [78, 114],
                    "prefix": "prefix_A",
                    "meeting_id": 35,
                },
                "motion_category/78": {
                    "name": "name_xSBwbHAT",
                    "parent_id": 111,
                    "motion_ids": [78, 85],
                    "meeting_id": 35,
                },
                "motion_category/114": {
                    "name": "name_pIObKJwT",
                    "parent_id": 111,
                    "prefix": "prefix_C",
                    "meeting_id": 35,
                },
            }
        )
        response = self.request(
            "motion_category.number_motions",
            {
                "id": 111,
            },
        )
        self.assert_status_code(response, 200)
        motion_78 = self.get_model("motion/78")
        assert motion_78.get("number") == "prefix_A 001"
        motion_85 = self.get_model("motion/85")
        assert motion_85.get("number") == "prefix_A 002"

    def test_check_amendments_error_case(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "meeting_1",
                    "motion_ids": [78, 85, 666],
                    "motion_category_ids": [111, 78, 114],
                    "is_active_in_organization_id": 1,
                },
                "motion/78": {"title": "title_NAZOknoM", "meeting_id": 1},
                "motion/85": {
                    "title": "title_MyMayxxr",
                    "lead_motion_id": 666,
                    "meeting_id": 1,
                },
                "motion/666": {"title": "title_XtzUEFdl", "meeting_id": 1},
                "motion_category/111": {
                    "name": "name_MKKAcYQu",
                    "child_ids": [78, 114],
                    "meeting_id": 1,
                },
                "motion_category/78": {
                    "name": "name_xSBwbHAT",
                    "parent_id": 111,
                    "motion_ids": [78, 85],
                    "meeting_id": 1,
                },
                "motion_category/114": {
                    "name": "name_pIObKJwT",
                    "parent_id": 111,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_category.number_motions",
            {
                "id": 111,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            'Amendment "85" cannot be numbered, because it\'s lead motion (666) is not in category 111 or any subcategory.',
            response.json["message"],
        )

    def test_3_categories_5_motions_some_with_lead_motion_ids(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motions_number_with_blank": True,
                    "motions_number_min_digits": 3,
                    "motions_amendments_prefix": "X",
                    "motion_category_ids": [1, 2, 3],
                    "motion_ids": [1, 2, 3, 4, 5],
                    "is_active_in_organization_id": 1,
                },
                "motion_category/1": {
                    "name": "name_category_1",
                    "child_ids": [2, 3],
                    "parent_id": None,
                    "meeting_id": 1,
                },
                "motion_category/2": {
                    "name": "name_category_2",
                    "child_ids": [],
                    "parent_id": 1,
                    "prefix": "A",
                    "meeting_id": 1,
                    "motion_ids": [1, 2],
                },
                "motion_category/3": {
                    "name": "name_category_3",
                    "child_ids": [],
                    "parent_id": 1,
                    "prefix": "B",
                    "meeting_id": 1,
                    "motion_ids": [3, 4, 5],
                },
                "motion/1": {
                    "title": "title_motion_1",
                    "category_id": 2,
                    "meeting_id": 1,
                },
                "motion/2": {
                    "title": "title_motion_2",
                    "category_id": 2,
                    "meeting_id": 1,
                },
                "motion/3": {
                    "title": "title_motion_3",
                    "category_id": 3,
                    "meeting_id": 1,
                },
                "motion/4": {
                    "title": "title_motion_4",
                    "category_id": 3,
                    "meeting_id": 1,
                    "lead_motion_id": 3,
                },
                "motion/5": {
                    "title": "title_motion_5",
                    "category_id": 3,
                    "meeting_id": 1,
                    "lead_motion_id": 3,
                },
            }
        )

        response = self.request(
            "motion_category.number_motions",
            {
                "id": 1,
            },
        )
        self.assert_status_code(response, 200)

        self.check_helper("motion/1", "A 001")
        self.check_helper("motion/2", "A 002")
        self.check_helper("motion/3", "B 003")
        self.check_helper("motion/4", "B 003 X 001")
        self.check_helper("motion/5", "B 003 X 002")

    def test_already_existing_number(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "meeting_1",
                    "motion_category_ids": [111],
                    "motion_ids": [69, 70],
                    "is_active_in_organization_id": 1,
                },
                "motion_category/111": {
                    "name": "name_MKKAcYQu",
                    "prefix": "prefix_A",
                    "motion_ids": [69],
                    "meeting_id": 1,
                },
                "motion/69": {
                    "title": "title_NAZOknoM",
                    "category_id": 111,
                    "meeting_id": 1,
                },
                "motion/70": {
                    "title": "title_NAZOknoM",
                    "meeting_id": 1,
                    "number": "prefix_A1",
                },
            }
        )
        response = self.request(
            "motion_category.number_motions",
            {
                "id": 111,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            'Numbering aborted because the motion identifier "prefix_A1" already exists.',
            response.json["message"],
        )

    def test_sort_categories(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_category_ids": [1, 2, 3, 4],
                    "motion_ids": [1, 2, 3],
                    "is_active_in_organization_id": 1,
                },
                "motion_category/1": {
                    "name": "category_1",
                    "meeting_id": 1,
                    "parent_id": None,
                    "child_ids": [2, 3, 4],
                },
                "motion_category/2": {
                    "name": "category_2",
                    "meeting_id": 1,
                    "parent_id": 1,
                    "child_ids": [],
                    "prefix": "C",
                    "weight": 100,
                    "motion_ids": [1],
                },
                "motion_category/3": {
                    "name": "category_3",
                    "meeting_id": 1,
                    "parent_id": 1,
                    "child_ids": [],
                    "prefix": "A",
                    "weight": 1,
                    "motion_ids": [2],
                },
                "motion_category/4": {
                    "name": "category_4",
                    "meeting_id": 1,
                    "parent_id": 1,
                    "child_ids": [],
                    "prefix": "B",
                    "weight": 10,
                    "motion_ids": [3],
                },
                "motion/1": {"title": "m1", "category_id": 2, "meeting_id": 1},
                "motion/2": {"title": "m2", "category_id": 3, "meeting_id": 1},
                "motion/3": {"title": "m3", "category_id": 4, "meeting_id": 1},
            }
        )
        response = self.request(
            "motion_category.number_motions",
            {
                "id": 1,
            },
        )
        self.assert_status_code(response, 200)

        self.check_helper("motion/1", "C3")
        self.check_helper("motion/2", "A1")
        self.check_helper("motion/3", "B2")

    def check_helper(self, model_str: str, excepted_number: str) -> None:
        motion = self.get_model(model_str)
        assert motion.get("number") == excepted_number

    def test_sort_motions(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_category_ids": [1],
                    "motion_ids": [1, 2, 3],
                    "is_active_in_organization_id": 1,
                },
                "motion_category/1": {
                    "name": "category_1",
                    "meeting_id": 1,
                    "parent_id": None,
                    "child_ids": [],
                    "motion_ids": [1, 2, 3],
                },
                "motion/1": {
                    "title": "m1",
                    "category_id": 1,
                    "meeting_id": 1,
                    "category_weight": 100,
                },
                "motion/2": {
                    "title": "m2",
                    "category_id": 1,
                    "meeting_id": 1,
                    "category_weight": 10,
                },
                "motion/3": {
                    "title": "m3",
                    "category_id": 1,
                    "meeting_id": 1,
                    "category_weight": 1,
                },
            }
        )
        response = self.request(
            "motion_category.number_motions",
            {
                "id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.check_helper("motion/1", "3")
        self.check_helper("motion/2", "2")
        self.check_helper("motion/3", "1")

    def test_stop_prefix_lookup_at_main_category(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_category_ids": [1, 2],
                    "motion_ids": [1],
                    "is_active_in_organization_id": 1,
                },
                "motion_category/1": {
                    "name": "category_1",
                    "meeting_id": 1,
                    "parent_id": None,
                    "child_ids": [2],
                    "motion_ids": [],
                    "prefix": "A",
                },
                "motion_category/2": {
                    "name": "category_2",
                    "meeting_id": 1,
                    "parent_id": 1,
                    "child_ids": [],
                    "motion_ids": [1],
                },
                "motion/1": {
                    "title": "m1",
                    "category_id": 2,
                    "meeting_id": 1,
                    "category_weight": 100,
                },
            }
        )

        response = self.request(
            "motion_category.number_motions",
            {
                "id": 2,
            },
        )
        self.assert_status_code(response, 200)
        self.check_helper("motion/1", "1")

    def test_invalid_id(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_category_ids": [1, 2],
                    "motion_ids": [1],
                    "is_active_in_organization_id": 1,
                },
                "motion_category/1": {
                    "name": "category_1",
                    "meeting_id": 1,
                    "parent_id": None,
                    "child_ids": [2],
                    "motion_ids": [],
                    "prefix": "A",
                },
                "motion_category/2": {
                    "name": "category_2",
                    "meeting_id": 1,
                    "parent_id": 1,
                    "child_ids": [],
                    "motion_ids": [1],
                },
                "motion/1": {
                    "title": "m1",
                    "category_id": 2,
                    "meeting_id": 1,
                    "category_weight": 100,
                },
            }
        )

        response = self.request(
            "motion_category.number_motions",
            {
                "id": 222,
            },
        )
        self.assert_status_code(response, 400)
        assert "Model 'motion_category/222' does not exist." in response.json.get(
            "message", ""
        )

    def test_number_motions_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_category.number_motions",
            {"id": 111},
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
            self.permission_test_models,
            "motion_category.number_motions",
            {"id": 111},
        )
