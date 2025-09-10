from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionSortActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(222)
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion/22": {
                "title": "motion22",
                "sequential_number": 22,
                "state_id": 1,
                "meeting_id": 1,
            },
            "list_of_speakers/23": {
                "content_object_id": "motion/22",
                "sequential_number": 11,
                "meeting_id": 1,
            },
        }

    def test_sort_single_node_correct(self) -> None:
        self.create_motion(222, 22)
        response = self.request(
            "motion.sort", {"meeting_id": 222, "tree": [{"id": 22}]}
        )
        self.assert_status_code(response, 200)
        self.assertEqual("Actions handled successfully", response.json["message"])
        self.assert_model_exists(
            "motion/22",
            {
                "sort_weight": 1,
                "sort_parent_id": None,
                "sort_child_ids": None,
            },
        )

    def test_sort_not_all_sorted(self) -> None:
        self.create_motion(222, 22)
        self.create_motion(222, 23)
        response = self.request(
            "motion.sort", {"meeting_id": 222, "tree": [{"id": 22}]}
        )
        self.assert_status_code(response, 400)
        self.assertEqual("Did not recieve 2 ids, got 1.", response.json["message"])

    def test_sort_complex_correct(self) -> None:
        self.create_motion(222, 1)
        self.create_motion(222, 11)
        self.create_motion(222, 12)
        self.create_motion(222, 21)
        self.create_motion(222, 22)
        self.create_motion(222, 23)

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
        self.create_motion(222, 1)
        self.create_motion(222, 11)
        self.create_motion(222, 12)
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
        self.assertEqual("Duplicate id in sort tree: 12", response.json["message"])

    def test_sort_circle_fail(self) -> None:
        self.create_motion(222, 1)
        self.create_motion(222, 11)
        self.create_motion(222, 12)

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
        self.assertEqual("Duplicate id in sort tree: 1", response.json["message"])

    def test_small_tree_correct(self) -> None:
        self.create_motion(222, 1)
        self.create_motion(222, 11)
        self.create_motion(222, 12)

        small_tree_data = {
            "meeting_id": 222,
            "tree": [{"id": 1, "children": [{"id": 11}, {"id": 12}]}],
        }
        response = self.request("motion.sort", small_tree_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1",
            {
                "sort_weight": 1,
                "sort_parent_id": None,
                "sort_child_ids": [11, 12],
            },
        )
        self.assert_model_exists(
            "motion/11",
            {
                "sort_weight": 1,
                "sort_parent_id": 1,
                "sort_child_ids": None,
            },
        )
        self.assert_model_exists(
            "motion/12",
            {
                "sort_weight": 2,
                "sort_parent_id": 1,
                "sort_child_ids": None,
            },
        )

    def test_extra_id(self) -> None:
        self.create_motion(222, 1)
        self.create_motion(222, 11)
        self.create_motion(222, 12)
        data = {
            "meeting_id": 222,
            "tree": [{"id": 1, "children": [{"id": 11}, {"id": 12}, {"id": 111}]}],
        }
        response = self.request("motion.sort", data)
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Id in sort tree does not exist: 111", response.json["message"]
        )

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
