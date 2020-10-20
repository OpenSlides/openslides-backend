from tests.system.action.base import BaseActionTestCase


class MediafileUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model("group/7", {"name": "group_LxAHErRs", "user_ids": []})
        self.create_model(
            "mediafile/111", {"title": "title_srtgb123"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.update",
                    "data": [
                        {"id": 111, "title": "title_Xcdfgee", "access_group_ids": [7]}
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        model = self.get_model("mediafile/111")
        assert model.get("title") == "title_Xcdfgee"
        assert model.get("access_group_ids") == [7]

    def test_update_parent(self) -> None:
        self.create_model("group/7", {"name": "group_LxAHErRs", "user_ids": []})
        self.create_model(
            "mediafile/110", {"title": "title_srtgb199", "child_ids": [111]}
        )
        self.create_model(
            "mediafile/111", {"title": "title_srtgb123", "parent_id": 110},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.update",
                    "data": [
                        {"id": 111, "title": "title_Xcdfgee", "access_group_ids": [7]}
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        model = self.get_model("mediafile/111")
        assert model.get("title") == "title_Xcdfgee"
        assert model.get("access_group_ids") == [7]
        assert model.get("inherited_access_group_ids") == [7]
        assert model.get("has_inherited_access_groups") is True

    def test_update_parent_inherited_list(self) -> None:
        self.create_model("group/7", {"name": "group_LxAHErRs", "user_ids": []})
        self.create_model("group/8", {"name": "group_sdfafd", "user_ids": []})
        self.create_model(
            "mediafile/110",
            {
                "title": "title_srtgb199",
                "child_ids": [111],
                "inherited_access_group_ids": [8],
                "has_inherited_access_groups": True,
            },
        )
        self.create_model(
            "mediafile/111", {"title": "title_srtgb123", "parent_id": 110},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.update",
                    "data": [
                        {"id": 111, "title": "title_Xcdfgee", "access_group_ids": [7]}
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        model = self.get_model("mediafile/111")
        assert model.get("title") == "title_Xcdfgee"
        assert model.get("access_group_ids") == [7]
        assert model.get("inherited_access_group_ids") == []
        assert model.get("has_inherited_access_groups") is True

    def test_update_parent_case1(self) -> None:
        self.create_model(
            "mediafile/110",
            {
                "title": "title_srtgb199",
                "child_ids": [111],
                "access_group_ids": [],
                "inherited_access_group_ids": [],
                "has_inherited_access_groups": False,
            },
        )
        self.create_model(
            "mediafile/111", {"title": "title_srtgb123", "parent_id": 110},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.update",
                    "data": [
                        {"id": 111, "title": "title_Xcdfgee", "access_group_ids": []}
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        model_child = self.get_model("mediafile/111")
        assert model_child.get("access_group_ids") == []
        assert model_child.get("inherited_access_group_ids") == []
        assert model_child.get("has_inherited_access_groups") is False

    def test_update_parent_case2(self) -> None:
        self.create_model("group/2", {"name": "group_LxAHErRs", "user_ids": []})
        self.create_model("group/4", {"name": "group_sdfafd", "user_ids": []})
        self.create_model(
            "mediafile/110",
            {
                "title": "title_srtgb199",
                "child_ids": [111],
                "inherited_access_group_ids": [2, 4],
                "access_group_ids": [2, 4],
                "has_inherited_access_groups": True,
            },
        )
        self.create_model(
            "mediafile/111", {"title": "title_srtgb123", "parent_id": 110},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.update",
                    "data": [
                        {"id": 111, "title": "title_Xcdfgee", "access_group_ids": []}
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        model = self.get_model("mediafile/111")
        assert model.get("access_group_ids") == []
        assert model.get("inherited_access_group_ids") == [2, 4]
        assert model.get("has_inherited_access_groups") is True

    def test_update_parent_case3(self) -> None:
        self.create_model("group/3", {"name": "group_LxAHErRs", "user_ids": []})
        self.create_model("group/6", {"name": "group_sdfafd", "user_ids": []})
        self.create_model(
            "mediafile/110",
            {
                "title": "title_srtgb199",
                "child_ids": [111],
                "inherited_access_group_ids": [],
                "access_group_ids": [],
                "has_inherited_access_groups": False,
            },
        )
        self.create_model(
            "mediafile/111", {"title": "title_srtgb123", "parent_id": 110},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.update",
                    "data": [
                        {
                            "id": 111,
                            "title": "title_Xcdfgee",
                            "access_group_ids": [3, 6],
                        }
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        model = self.get_model("mediafile/111")
        assert model.get("access_group_ids") == [3, 6]
        assert model.get("inherited_access_group_ids") == [3, 6]
        assert model.get("has_inherited_access_groups") is True

    def test_update_parent_case4(self) -> None:
        self.create_model("group/1", {"name": "group_LxAHErRs", "user_ids": []})
        self.create_model("group/2", {"name": "group_sdfafd", "user_ids": []})
        self.create_model("group/3", {"name": "group_ghjeei", "user_ids": []})
        self.create_model(
            "mediafile/110",
            {
                "title": "title_srtgb199",
                "child_ids": [111],
                "inherited_access_group_ids": [1, 2],
                "access_group_ids": [1, 2],
                "has_inherited_access_groups": True,
            },
        )
        self.create_model(
            "mediafile/111", {"title": "title_srtgb123", "parent_id": 110},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.update",
                    "data": [
                        {
                            "id": 111,
                            "title": "title_Xcdfgee",
                            "access_group_ids": [2, 3],
                        }
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        model = self.get_model("mediafile/111")
        assert model.get("access_group_ids") == [2, 3]
        assert model.get("inherited_access_group_ids") == [2]
        assert model.get("has_inherited_access_groups") is True

    def test_update_parent_case5(self) -> None:
        self.create_model("group/1", {"name": "group_LxAHErRs", "user_ids": []})
        self.create_model("group/2", {"name": "group_sdfafd", "user_ids": []})
        self.create_model("group/3", {"name": "group_ghjeei", "user_ids": []})
        self.create_model(
            "mediafile/110",
            {
                "title": "title_srtgb199",
                "child_ids": [111],
                "inherited_access_group_ids": [1, 2],
                "access_group_ids": [1, 2],
                "has_inherited_access_groups": True,
            },
        )
        self.create_model(
            "mediafile/111", {"title": "title_srtgb123", "parent_id": 110},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.update",
                    "data": [
                        {"id": 111, "title": "title_Xcdfgee", "access_group_ids": [3]}
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        model = self.get_model("mediafile/111")
        assert model.get("access_group_ids") == [3]
        assert model.get("inherited_access_group_ids") == []
        assert model.get("has_inherited_access_groups") is True

    def test_update_parent_inherited_true(self) -> None:
        self.create_model(
            "mediafile/110",
            {
                "title": "title_srtgb199",
                "child_ids": [111],
                "inherited_access_group_ids": [],
                "access_group_ids": [],
                "has_inherited_access_groups": True,
            },
        )
        self.create_model(
            "mediafile/111", {"title": "title_srtgb123", "parent_id": 110},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.update",
                    "data": [
                        {"id": 111, "title": "title_Xcdfgee", "access_group_ids": []}
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        model = self.get_model("mediafile/111")
        assert model.get("access_group_ids") == []
        assert model.get("inherited_access_group_ids") == []
        assert model.get("has_inherited_access_groups") is True

    def test_update_wrong_id(self) -> None:
        self.create_model(
            "mediafile/111", {"title": "title_srtgb123"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.update",
                    "data": [{"id": 112, "title": "title_Xcdfgee"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("mediafile/111")
        assert model.get("title") == "title_srtgb123"
