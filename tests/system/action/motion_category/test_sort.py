from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCategorySortActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(222)
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_category/22": {
                "name": "category 22",
                "meeting_id": 1,
                "sequential_number": 22,
            },
        }

    def create_motion_category(self, base: int) -> None:
        self.set_models(
            {
                f"motion_category/{base}": {
                    "name": f"category {base}",
                    "meeting_id": 222,
                    "sequential_number": base,
                }
            }
        )

    def test_sort_singe_node_correct(self) -> None:
        self.create_motion_category(22)
        response = self.request(
            "motion_category.sort", {"meeting_id": 222, "tree": [{"id": 22}]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_category/22",
            {"weight": 1, "parent_id": None, "child_ids": None, "level": 0},
        )

    def test_sort_not_all_sorted(self) -> None:
        self.create_motion_category(22)
        self.create_motion_category(23)
        response = self.request(
            "motion_category.sort", {"meeting_id": 222, "tree": [{"id": 22}]}
        )
        self.assert_status_code(response, 400)
        self.assertEqual("Did not recieve 2 ids, got 1.", response.json["message"])

    def test_sort_complex_correct(self) -> None:
        self.create_motion_category(1)
        self.create_motion_category(11)
        self.create_motion_category(12)
        self.create_motion_category(21)
        self.create_motion_category(22)
        self.create_motion_category(23)

        valid_data = {
            "meeting_id": 222,
            "tree": [
                {
                    "id": 1,
                    "children": [
                        {"id": 11, "children": [{"id": 21}]},
                        {"id": 12, "children": [{"id": 22}, {"id": 23}]},
                    ],
                }
            ],
        }

        response = self.request("motion_category.sort", valid_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_category/1", {"level": 0, "weight": 1})
        self.assert_model_exists("motion_category/11", {"level": 1, "weight": 1})
        self.assert_model_exists("motion_category/12", {"level": 1, "weight": 2})
        self.assert_model_exists("motion_category/21", {"level": 2, "weight": 1})
        self.assert_model_exists("motion_category/22", {"level": 2, "weight": 1})
        self.assert_model_exists("motion_category/23", {"level": 2, "weight": 2})

    def test_sort_not_a_tree(self) -> None:
        self.create_motion_category(1)
        self.create_motion_category(11)
        self.create_motion_category(12)

        not_tree_data = {
            "meeting_id": 222,
            "tree": [
                {
                    "id": 1,
                    "children": [{"id": 11, "children": [{"id": 12}]}, {"id": 12}],
                }
            ],
        }
        response = self.request("motion_category.sort", not_tree_data)
        self.assert_status_code(response, 400)
        self.assertEqual("Duplicate id in sort tree: 12", response.json["message"])

    def test_sort_circle_fail(self) -> None:
        self.create_motion_category(1)
        self.create_motion_category(11)
        self.create_motion_category(12)

        circle_data = {
            "meeting_id": 222,
            "tree": [
                {
                    "id": 1,
                    "children": [
                        {"id": 11, "children": [{"id": 12, "children": [{"id": 1}]}]}
                    ],
                }
            ],
        }
        response = self.request("motion_category.sort", circle_data)
        self.assert_status_code(response, 400)
        self.assertEqual("Duplicate id in sort tree: 1", response.json["message"])

    def test_small_tree_correct(self) -> None:
        self.create_motion_category(1)
        self.create_motion_category(11)
        self.create_motion_category(12)

        small_tree_data = {
            "meeting_id": 222,
            "tree": [{"id": 1, "children": [{"id": 11}, {"id": 12}]}],
        }
        response = self.request("motion_category.sort", small_tree_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_category/1",
            {"weight": 1, "parent_id": None, "child_ids": [11, 12], "level": 0},
        )
        self.assert_model_exists(
            "motion_category/11",
            {"weight": 1, "parent_id": 1, "child_ids": None, "level": 1},
        )
        self.assert_model_exists(
            "motion_category/12",
            {"weight": 2, "parent_id": 1, "child_ids": None, "level": 1},
        )

    def test_sort_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_category.sort",
            {"meeting_id": 1, "tree": [{"id": 22}]},
        )

    def test_sort_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_category.sort",
            {"meeting_id": 1, "tree": [{"id": 22}]},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_sort_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion_category.sort",
            {"meeting_id": 1, "tree": [{"id": 22}]},
        )
