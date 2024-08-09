from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionSortActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion/22": {"meeting_id": 1, "title": "test1"},
        }

    def test_sort_singe_node_correct(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion/22": {"meeting_id": 222, "title": "test1"},
            }
        )
        response = self.request(
            "motion.sort", {"meeting_id": 222, "tree": [{"id": 22}]}
        )
        self.assert_status_code(response, 200)
        assert "Actions handled successfully" in response.json["message"]
        model_22 = self.get_model("motion/22")
        assert model_22.get("sort_weight") == 1
        assert model_22.get("sort_parent_id") is None
        assert model_22.get("sort_child_ids") == []

    def test_sort_not_all_sorted(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion/22": {"meeting_id": 222, "title": "test1"},
                "motion/23": {"meeting_id": 222, "title": "test"},
            }
        )
        response = self.request(
            "motion.sort", {"meeting_id": 222, "tree": [{"id": 22}]}
        )
        self.assert_status_code(response, 400)
        assert "Did not recieve 2 ids, got 1" in response.json["message"]

    def test_sort_complex_correct(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion/1": {"meeting_id": 222, "title": "test_root"},
                "motion/11": {"meeting_id": 222, "title": "test_1_1"},
                "motion/12": {"meeting_id": 222, "title": "test_1_2"},
                "motion/21": {"meeting_id": 222, "title": "test_2_1"},
                "motion/22": {"meeting_id": 222, "title": "test_2_2"},
                "motion/23": {"meeting_id": 222, "title": "test_2_3"},
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

        response = self.request("motion.sort", valid_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"sort_weight": 1})
        self.assert_model_exists("motion/11", {"sort_weight": 1})
        self.assert_model_exists("motion/12", {"sort_weight": 2})
        self.assert_model_exists("motion/21", {"sort_weight": 1})
        self.assert_model_exists("motion/22", {"sort_weight": 1})
        self.assert_model_exists("motion/23", {"sort_weight": 2})

    def test_sort_not_a_tree(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion/1": {"meeting_id": 222, "title": "test_root"},
                "motion/11": {"meeting_id": 222, "title": "test_1_1"},
                "motion/12": {"meeting_id": 222, "title": "test_1_2"},
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
        response = self.request("motion.sort", not_tree_data)
        self.assert_status_code(response, 400)
        assert "Duplicate id in sort tree: 12" in response.json["message"]

    def test_sort_circle_fail(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion/1": {"meeting_id": 222, "title": "test_root"},
                "motion/11": {"meeting_id": 222, "title": "test_1_1"},
                "motion/12": {"meeting_id": 222, "title": "test_1_2"},
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
        response = self.request("motion.sort", circle_data)
        self.assert_status_code(response, 400)
        assert "Duplicate id in sort tree: 1" in response.json["message"]

    def test_small_tree_correct(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion/1": {"meeting_id": 222, "title": "test_root"},
                "motion/11": {"meeting_id": 222, "title": "test_1_1"},
                "motion/12": {"meeting_id": 222, "title": "test_1_2"},
            }
        )

        small_tree_data = {
            "meeting_id": 222,
            "tree": [{"id": 1, "children": [{"id": 11}, {"id": 12}]}],
        }
        response = self.request("motion.sort", small_tree_data)
        self.assert_status_code(response, 200)
        model_1 = self.get_model("motion/1")
        assert model_1.get("sort_weight") == 1
        assert model_1.get("sort_parent_id") is None
        assert model_1.get("sort_child_ids") == [11, 12]
        model_11 = self.get_model("motion/11")
        assert model_11.get("sort_weight") == 1
        assert model_11.get("sort_parent_id") == 1
        assert model_11.get("sort_child_ids") == []
        model_12 = self.get_model("motion/12")
        assert model_12.get("sort_weight") == 2
        assert model_12.get("sort_parent_id") == 1
        assert model_12.get("sort_child_ids") == []

    def test_extra_id(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion/1": {"meeting_id": 222, "title": "test_root"},
                "motion/11": {"meeting_id": 222, "title": "test_1_1"},
                "motion/12": {"meeting_id": 222, "title": "test_1_2"},
            }
        )

        data = {
            "meeting_id": 222,
            "tree": [{"id": 1, "children": [{"id": 11}, {"id": 12}, {"id": 111}]}],
        }
        response = self.request("motion.sort", data)
        self.assert_status_code(response, 400)
        assert "Id in sort tree does not exist: 111" in response.json["message"]

    def test_sort_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.sort",
            {"meeting_id": 1, "tree": [{"id": 22}]},
        )

    def test_sort_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.sort",
            {"meeting_id": 1, "tree": [{"id": 22}]},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_sort_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion.sort",
            {"meeting_id": 1, "tree": [{"id": 22}]},
        )
