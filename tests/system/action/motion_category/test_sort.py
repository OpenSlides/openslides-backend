from tests.system.action.base import BaseActionTestCase


class MotionCategorySortActionTest(BaseActionTestCase):
    def test_sort_singe_node_correct(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model("motion_category/22", {"meeting_id": 222, "title": "test1"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_category.sort",
                    "data": {"meeting_id": 222, "tree": [{"id": 22}]},
                }
            ],
        )
        self.assert_status_code(response, 200)
        assert "Action handled successfully" in str(response.data)
        model_22 = self.get_model("motion_category/22")
        assert model_22.get("weight") == 2
        assert model_22.get("parent_id") is None
        assert model_22.get("child_ids") == []

    def test_sort_not_all_sorted(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model("motion_category/22", {"meeting_id": 222, "title": "test1"})
        self.create_model("motion_category/23", {"meeting_id": 222, "title": "test"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_category.sort",
                    "data": {"meeting_id": 222, "tree": [{"id": 22}]},
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Did not recieve 2 ids, got 1" in str(response.data)

    def test_sort_complex_correct(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_category/1", {"meeting_id": 222, "title": "test_root"}
        )
        self.create_model(
            "motion_category/11", {"meeting_id": 222, "title": "test_1_1"}
        )
        self.create_model(
            "motion_category/12", {"meeting_id": 222, "title": "test_1_2"}
        )
        self.create_model(
            "motion_category/21", {"meeting_id": 222, "title": "test_2_1"}
        )
        self.create_model(
            "motion_category/22", {"meeting_id": 222, "title": "test_2_2"}
        )
        self.create_model(
            "motion_category/23", {"meeting_id": 222, "title": "test_2_3"}
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

        response = self.client.post(
            "/", json=[{"action": "motion_category.sort", "data": valid_data}],
        )
        self.assert_status_code(response, 200)
        fqids_in_preorder = [
            "motion_category/1",
            "motion_category/11",
            "motion_category/21",
            "motion_category/12",
            "motion_category/22",
            "motion_category/23",
        ]
        weight = 2
        for fqid in fqids_in_preorder:
            model = self.get_model(fqid)
            assert model.get("weight") == weight
            weight += 2

    def test_sort_not_a_tree(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_category/1", {"meeting_id": 222, "title": "test_root"}
        )
        self.create_model(
            "motion_category/11", {"meeting_id": 222, "title": "test_1_1"}
        )
        self.create_model(
            "motion_category/12", {"meeting_id": 222, "title": "test_1_2"}
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
        response = self.client.post(
            "/", json=[{"action": "motion_category.sort", "data": not_tree_data}],
        )
        self.assert_status_code(response, 400)
        assert "Duplicate id in sort tree: 12" in str(response.data)

    def test_sort_circle_fail(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_category/1", {"meeting_id": 222, "title": "test_root"}
        )
        self.create_model(
            "motion_category/11", {"meeting_id": 222, "title": "test_1_1"}
        )
        self.create_model(
            "motion_category/12", {"meeting_id": 222, "title": "test_1_2"}
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
        response = self.client.post(
            "/", json=[{"action": "motion_category.sort", "data": circle_data}],
        )
        self.assert_status_code(response, 400)
        assert "Duplicate id in sort tree: 1" in str(response.data)

    def test_small_tree_correct(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_category/1", {"meeting_id": 222, "title": "test_root"}
        )
        self.create_model(
            "motion_category/11", {"meeting_id": 222, "title": "test_1_1"}
        )
        self.create_model(
            "motion_category/12", {"meeting_id": 222, "title": "test_1_2"}
        )

        small_tree_data = {
            "meeting_id": 222,
            "tree": [{"id": 1, "children": [{"id": 11}, {"id": 12}]}],
        }
        response = self.client.post(
            "/", json=[{"action": "motion_category.sort", "data": small_tree_data}],
        )
        self.assert_status_code(response, 200)
        model_1 = self.get_model("motion_category/1")
        assert model_1.get("weight") == 2
        assert model_1.get("parent_id") is None
        assert model_1.get("child_ids") == [11, 12]
        model_11 = self.get_model("motion_category/11")
        assert model_11.get("weight") == 4
        assert model_11.get("parent_id") == 1
        assert model_11.get("child_ids") == []
        model_12 = self.get_model("motion_category/12")
        assert model_12.get("weight") == 6
        assert model_12.get("parent_id") == 1
        assert model_12.get("child_ids") == []
