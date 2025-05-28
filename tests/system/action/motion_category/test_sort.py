from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCategorySortActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(222)
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_category/22": {"meeting_id": 1},
        }

    def test_sort_singe_node_correct(self) -> None:
        self.set_models(
            {
                "motion_category/22": {"meeting_id": 222},
            }
        )
        response = self.request(
            "motion_category.sort", {"meeting_id": 222, "tree": [{"id": 22}]}
        )
        self.assert_status_code(response, 200)
        assert "Actions handled successfully" in response.json["message"]
        model_22 = self.get_model("motion_category/22")
        assert model_22.get("weight") == 1
        assert model_22.get("parent_id") is None
        assert model_22.get("child_ids") == []
        assert model_22.get("level") == 0

    def test_sort_not_all_sorted(self) -> None:
        self.set_models(
            {
                "motion_category/22": {"meeting_id": 222},
                "motion_category/23": {"meeting_id": 222},
            }
        )
        response = self.request(
            "motion_category.sort", {"meeting_id": 222, "tree": [{"id": 22}]}
        )
        self.assert_status_code(response, 400)
        assert "Did not recieve 2 ids, got 1" in response.json["message"]

    def test_sort_complex_correct(self) -> None:
        self.set_models(
            {
                "motion_category/1": {"meeting_id": 222},
                "motion_category/11": {"meeting_id": 222},
                "motion_category/12": {"meeting_id": 222},
                "motion_category/21": {"meeting_id": 222},
                "motion_category/22": {"meeting_id": 222},
                "motion_category/23": {"meeting_id": 222},
            }
        )

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
        self.set_models(
            {
                "motion_category/1": {"meeting_id": 222},
                "motion_category/11": {"meeting_id": 222},
                "motion_category/12": {"meeting_id": 222},
            }
        )

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
        assert "Duplicate id in sort tree: 12" in response.json["message"]

    def test_sort_circle_fail(self) -> None:
        self.set_models(
            {
                "motion_category/1": {"meeting_id": 222},
                "motion_category/11": {"meeting_id": 222},
                "motion_category/12": {"meeting_id": 222},
            }
        )

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
        assert "Duplicate id in sort tree: 1" in response.json["message"]

    def test_small_tree_correct(self) -> None:
        self.set_models(
            {
                "motion_category/1": {"meeting_id": 222},
                "motion_category/11": {"meeting_id": 222},
                "motion_category/12": {"meeting_id": 222},
            }
        )

        small_tree_data = {
            "meeting_id": 222,
            "tree": [{"id": 1, "children": [{"id": 11}, {"id": 12}]}],
        }
        response = self.request("motion_category.sort", small_tree_data)
        self.assert_status_code(response, 200)
        model_1 = self.get_model("motion_category/1")
        assert model_1.get("weight") == 1
        assert model_1.get("parent_id") is None
        assert model_1.get("child_ids") == [11, 12]
        assert model_1.get("level") == 0
        model_11 = self.get_model("motion_category/11")
        assert model_11.get("weight") == 1
        assert model_11.get("parent_id") == 1
        assert model_11.get("child_ids") == []
        assert model_11.get("level") == 1
        model_12 = self.get_model("motion_category/12")
        assert model_12.get("weight") == 2
        assert model_12.get("parent_id") == 1
        assert model_12.get("child_ids") == []
        assert model_12.get("level") == 1

    def test_with_deleted_model(self) -> None:
        self.set_models(
            {
                "meeting/222": {"motion_category_ids": [2, 3]},
            }
        )
        self.create_model("motion_category/1", {"meeting_id": 222}, deleted=True)
        self.set_models(
            {
                "motion_category/2": {"meeting_id": 222},
                "motion_category/3": {"meeting_id": 222},
            }
        )
        response = self.request(
            "motion_category.sort", {"meeting_id": 222, "tree": [{"id": 2}, {"id": 3}]}
        )
        self.assert_status_code(response, 200)
        assert "Actions handled successfully" in response.json["message"]
        category_1 = self.get_model("motion_category/1")
        assert category_1.get("weight") is None
        category_2 = self.get_model("motion_category/2")
        assert category_2.get("weight") == 1
        category_3 = self.get_model("motion_category/3")
        assert category_3.get("weight") == 2

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
