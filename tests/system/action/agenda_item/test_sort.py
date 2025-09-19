from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class AgendaItemSortActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(222)

    def test_sort_single_node_correct(self) -> None:
        self.set_models(
            {
                "topic/2": {
                    "meeting_id": 222,
                    "title": "jungle",
                    "sequential_number": 2,
                },
                "agenda_item/22": {
                    "meeting_id": 222,
                    "content_object_id": "topic/2",
                    "comment": "test1",
                },
            }
        )
        response = self.request(
            "agenda_item.sort", {"meeting_id": 222, "tree": [{"id": 22}]}
        )
        self.assert_status_code(response, 200)
        assert "Actions handled successfully" in response.json["message"]
        model_22 = self.get_model("agenda_item/22")
        assert model_22.get("weight") == 1
        assert model_22.get("parent_id") is None
        assert model_22.get("child_ids") is None
        assert model_22.get("level") == 0

    def test_sort_not_all_sorted(self) -> None:
        self.set_models(
            {
                "topic/1": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 1,
                },
                "topic/2": {
                    "meeting_id": 222,
                    "title": "jungle",
                    "sequential_number": 2,
                },
                "agenda_item/22": {
                    "meeting_id": 222,
                    "content_object_id": "topic/1",
                    "comment": "test1",
                },
                "agenda_item/23": {
                    "meeting_id": 222,
                    "content_object_id": "topic/2",
                    "comment": "test",
                },
            }
        )
        response = self.request(
            "agenda_item.sort", {"meeting_id": 222, "tree": [{"id": 22}]}
        )
        self.assert_status_code(response, 400)
        assert "Did not recieve 2 ids, got 1" in response.json["message"]

    def test_sort_complex_correct(self) -> None:
        self.set_models(
            {
                "topic/1": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 1,
                },
                "topic/2": {
                    "meeting_id": 222,
                    "title": "jungle",
                    "sequential_number": 2,
                },
                "topic/3": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 3,
                },
                "topic/4": {
                    "meeting_id": 222,
                    "title": "jungle",
                    "sequential_number": 4,
                },
                "topic/5": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 5,
                },
                "topic/6": {
                    "meeting_id": 222,
                    "title": "jungle",
                    "sequential_number": 6,
                },
                "agenda_item/1": {
                    "meeting_id": 222,
                    "comment": "test_root",
                    "content_object_id": "topic/1",
                },
                "agenda_item/11": {
                    "meeting_id": 222,
                    "comment": "test_1_1",
                    "content_object_id": "topic/2",
                },
                "agenda_item/12": {
                    "meeting_id": 222,
                    "comment": "test_1_2",
                    "content_object_id": "topic/3",
                },
                "agenda_item/21": {
                    "meeting_id": 222,
                    "comment": "test_2_1",
                    "content_object_id": "topic/4",
                },
                "agenda_item/22": {
                    "meeting_id": 222,
                    "comment": "test_2_2",
                    "content_object_id": "topic/5",
                },
                "agenda_item/23": {
                    "meeting_id": 222,
                    "comment": "test_2_3",
                    "content_object_id": "topic/6",
                },
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

        response = self.request("agenda_item.sort", valid_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("agenda_item/1", {"level": 0, "weight": 1})
        self.assert_model_exists("agenda_item/11", {"level": 1, "weight": 1})
        self.assert_model_exists("agenda_item/12", {"level": 1, "weight": 2})
        self.assert_model_exists("agenda_item/21", {"level": 2, "weight": 1})
        self.assert_model_exists("agenda_item/22", {"level": 2, "weight": 1})
        self.assert_model_exists("agenda_item/23", {"level": 2, "weight": 2})

    def test_sort_not_a_tree(self) -> None:
        self.set_models(
            {
                "topic/1": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 1,
                },
                "topic/2": {
                    "meeting_id": 222,
                    "title": "jungle",
                    "sequential_number": 2,
                },
                "topic/3": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 3,
                },
                "agenda_item/1": {
                    "meeting_id": 222,
                    "comment": "test_root",
                    "content_object_id": "topic/1",
                },
                "agenda_item/11": {
                    "meeting_id": 222,
                    "comment": "test_1_1",
                    "content_object_id": "topic/2",
                },
                "agenda_item/12": {
                    "meeting_id": 222,
                    "comment": "test_1_2",
                    "content_object_id": "topic/3",
                },
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
        response = self.request("agenda_item.sort", not_tree_data)
        self.assert_status_code(response, 400)
        assert "Duplicate id in sort tree: 12" in response.json["message"]

    def test_sort_circle_fail(self) -> None:
        self.set_models(
            {
                "topic/1": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 1,
                },
                "topic/2": {
                    "meeting_id": 222,
                    "title": "jungle",
                    "sequential_number": 2,
                },
                "topic/3": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 3,
                },
                "agenda_item/1": {
                    "meeting_id": 222,
                    "comment": "test_root",
                    "content_object_id": "topic/1",
                },
                "agenda_item/11": {
                    "meeting_id": 222,
                    "comment": "test_1_1",
                    "content_object_id": "topic/2",
                },
                "agenda_item/12": {
                    "meeting_id": 222,
                    "comment": "test_1_2",
                    "content_object_id": "topic/3",
                },
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
        response = self.request("agenda_item.sort", circle_data)
        self.assert_status_code(response, 400)
        assert "Duplicate id in sort tree: 1" in response.json["message"]

    def test_small_tree_correct(self) -> None:
        self.set_models(
            {
                "topic/1": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 1,
                },
                "topic/2": {
                    "meeting_id": 222,
                    "title": "jungle",
                    "sequential_number": 2,
                },
                "topic/3": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 3,
                },
                "agenda_item/1": {
                    "meeting_id": 222,
                    "comment": "test_root",
                    "content_object_id": "topic/1",
                },
                "agenda_item/11": {
                    "meeting_id": 222,
                    "comment": "test_1_1",
                    "content_object_id": "topic/2",
                },
                "agenda_item/12": {
                    "meeting_id": 222,
                    "comment": "test_1_2",
                    "content_object_id": "topic/3",
                },
            }
        )

        small_tree_data = {
            "meeting_id": 222,
            "tree": [{"id": 1, "children": [{"id": 11}, {"id": 12}]}],
        }
        response = self.request("agenda_item.sort", small_tree_data)
        self.assert_status_code(response, 200)
        model_1 = self.get_model("agenda_item/1")
        assert model_1.get("weight") == 1
        assert model_1.get("parent_id") is None
        assert model_1.get("child_ids") == [11, 12]
        assert model_1.get("level") == 0
        model_11 = self.get_model("agenda_item/11")
        assert model_11.get("weight") == 1
        assert model_11.get("parent_id") == 1
        assert model_11.get("child_ids") is None
        assert model_11.get("level") == 1
        model_12 = self.get_model("agenda_item/12")
        assert model_12.get("weight") == 2
        assert model_12.get("parent_id") == 1
        assert model_12.get("child_ids") is None
        assert model_12.get("level") == 1

    def test_sort_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "topic/1": {"meeting_id": 1, "title": "tropic", "sequential_number": 1},
                "agenda_item/22": {
                    "meeting_id": 1,
                    "comment": "test1",
                    "content_object_id": "topic/1",
                },
            },
            "agenda_item.sort",
            {"meeting_id": 1, "tree": [{"id": 22}]},
        )

    def test_sort_permissions(self) -> None:
        self.base_permission_test(
            {
                "topic/1": {"meeting_id": 1, "title": "tropic", "sequential_number": 1},
                "agenda_item/22": {
                    "meeting_id": 1,
                    "comment": "test1",
                    "content_object_id": "topic/1",
                },
            },
            "agenda_item.sort",
            {"meeting_id": 1, "tree": [{"id": 22}]},
            Permissions.AgendaItem.CAN_MANAGE,
        )

    def test_sort_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {
                "topic/1": {"meeting_id": 1, "title": "tropic", "sequential_number": 1},
                "agenda_item/22": {
                    "meeting_id": 1,
                    "comment": "test1",
                    "content_object_id": "topic/1",
                },
            },
            "agenda_item.sort",
            {"meeting_id": 1, "tree": [{"id": 22}]},
        )
