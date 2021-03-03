from tests.system.action.base import BaseActionTestCase


class MediafileUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models(
            {
                "group/7": {"name": "group_LxAHErRs", "user_ids": []},
                "mediafile/111": {"title": "title_srtgb123"},
            }
        )
        response = self.request(
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee", "access_group_ids": [7]},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("title") == "title_Xcdfgee"
        assert model.get("access_group_ids") == [7]
        assert model.get("inherited_access_group_ids") == [7]
        assert model.get("is_public") is False

    def test_update_children(self) -> None:
        self.set_models(
            {
                "group/7": {"name": "group_LxAHErRs", "user_ids": []},
                "mediafile/110": {
                    "title": "title_ekxORNiV",
                    "child_ids": [111],
                    "is_public": False,
                    "inherited_access_group_ids": [7],
                    "access_group_ids": [7],
                },
                "mediafile/111": {"title": "title_srtgb123", "parent_id": 110},
            }
        )
        response = self.request(
            "mediafile.update",
            {"id": 110, "title": "title_Xcdfgee", "access_group_ids": [7]},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("title") == "title_srtgb123"
        assert model.get("inherited_access_group_ids") == [7]
        assert model.get("is_public") is False

    def test_update_parent(self) -> None:
        self.set_models(
            {
                "group/7": {"name": "group_LxAHErRs", "user_ids": []},
                "mediafile/110": {"title": "title_srtgb199", "child_ids": [111]},
                "mediafile/111": {"title": "title_srtgb123", "parent_id": 110},
            }
        )
        response = self.request(
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee", "access_group_ids": [7]},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("title") == "title_Xcdfgee"
        assert model.get("access_group_ids") == [7]
        assert model.get("inherited_access_group_ids") == [7]
        assert model.get("is_public") is False

    def test_update_parent_inherited_list(self) -> None:
        self.set_models(
            {
                "group/7": {"name": "group_LxAHErRs", "user_ids": []},
                "group/8": {"name": "group_sdfafd", "user_ids": []},
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "inherited_access_group_ids": [8],
                    "is_public": False,
                },
                "mediafile/111": {"title": "title_srtgb123", "parent_id": 110},
            }
        )
        response = self.request(
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee", "access_group_ids": [7]},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("title") == "title_Xcdfgee"
        assert model.get("access_group_ids") == [7]
        assert model.get("inherited_access_group_ids") == []
        assert model.get("is_public") is False

    def test_update_parent_case1(self) -> None:
        self.set_models(
            {
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "access_group_ids": [],
                    "inherited_access_group_ids": [],
                    "is_public": True,
                },
                "mediafile/111": {"title": "title_srtgb123", "parent_id": 110},
            }
        )
        response = self.request(
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee", "access_group_ids": []},
        )
        self.assert_status_code(response, 200)
        model_child = self.get_model("mediafile/111")
        assert model_child.get("access_group_ids") == []
        assert model_child.get("inherited_access_group_ids") == []
        assert model_child.get("is_public") is True

    def test_update_parent_case2(self) -> None:
        self.set_models(
            {
                "group/2": {"name": "group_LxAHErRs", "user_ids": []},
                "group/4": {"name": "group_sdfafd", "user_ids": []},
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "inherited_access_group_ids": [2, 4],
                    "access_group_ids": [2, 4],
                    "is_public": False,
                },
                "mediafile/111": {"title": "title_srtgb123", "parent_id": 110},
            }
        )
        response = self.request(
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee", "access_group_ids": []},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("access_group_ids") == []
        assert model.get("inherited_access_group_ids") == [2, 4]
        assert model.get("is_public") is False

    def test_update_parent_case3(self) -> None:
        self.set_models(
            {
                "group/3": {"name": "group_LxAHErRs", "user_ids": []},
                "group/6": {"name": "group_sdfafd", "user_ids": []},
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "inherited_access_group_ids": [],
                    "access_group_ids": [],
                    "is_public": True,
                },
                "mediafile/111": {"title": "title_srtgb123", "parent_id": 110},
            }
        )
        response = self.request(
            "mediafile.update",
            {
                "id": 111,
                "title": "title_Xcdfgee",
                "access_group_ids": [3, 6],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("access_group_ids") == [3, 6]
        assert model.get("inherited_access_group_ids") == [3, 6]
        assert model.get("is_public") is False

    def test_update_parent_case4(self) -> None:
        self.set_models(
            {
                "group/1": {"name": "group_LxAHErRs", "user_ids": []},
                "group/2": {"name": "group_sdfafd", "user_ids": []},
                "group/3": {"name": "group_ghjeei", "user_ids": []},
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "inherited_access_group_ids": [1, 2],
                    "access_group_ids": [1, 2],
                    "is_public": False,
                },
                "mediafile/111": {"title": "title_srtgb123", "parent_id": 110},
            }
        )
        response = self.request(
            "mediafile.update",
            {
                "id": 111,
                "title": "title_Xcdfgee",
                "access_group_ids": [2, 3],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("access_group_ids") == [2, 3]
        assert model.get("inherited_access_group_ids") == [2]
        assert model.get("is_public") is False

    def test_update_parent_case5(self) -> None:
        self.set_models(
            {
                "group/1": {"name": "group_LxAHErRs", "user_ids": []},
                "group/2": {"name": "group_sdfafd", "user_ids": []},
                "group/3": {"name": "group_ghjeei", "user_ids": []},
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "inherited_access_group_ids": [1, 2],
                    "access_group_ids": [1, 2],
                    "is_public": False,
                },
                "mediafile/111": {"title": "title_srtgb123", "parent_id": 110},
            }
        )
        response = self.request(
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee", "access_group_ids": [3]},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("access_group_ids") == [3]
        assert model.get("inherited_access_group_ids") == []
        assert model.get("is_public") is False

    def test_update_parent_inherited_true(self) -> None:
        self.set_models(
            {
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "inherited_access_group_ids": [],
                    "access_group_ids": [],
                    "is_public": False,
                },
                "mediafile/111": {"title": "title_srtgb123", "parent_id": 110},
            }
        )
        response = self.request(
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee", "access_group_ids": []},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("access_group_ids") == []
        assert model.get("inherited_access_group_ids") == []
        assert model.get("is_public") is False

    def test_update_wrong_id(self) -> None:
        self.create_model(
            "mediafile/111",
            {"title": "title_srtgb123"},
        )
        response = self.request(
            "mediafile.update", {"id": 112, "title": "title_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("mediafile/111")
        assert model.get("title") == "title_srtgb123"

    def test_update_parent_and_children(self) -> None:
        self.set_models(
            {
                "group/7": {"name": "group_LxAHErRs", "user_ids": []},
                "mediafile/110": {"title": "title_srtgb199", "child_ids": [111]},
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "child_ids": [112],
                },
                "mediafile/112": {
                    "title": "title_srtgb123",
                    "parent_id": 111,
                    "access_group_ids": [7],
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee", "access_group_ids": [7]},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("title") == "title_Xcdfgee"
        assert model.get("access_group_ids") == [7]
        assert model.get("inherited_access_group_ids") == [7]
        assert model.get("is_public") is False
        child = self.get_model("mediafile/112")
        assert child.get("access_group_ids") == [7]
        assert child.get("inherited_access_group_ids") == [7]
        assert child.get("is_public") is False

    def test_update_parent_and_children_2(self) -> None:
        self.set_models(
            {
                "group/7": {"name": "group_LxAHErRs", "user_ids": []},
                "mediafile/110": {"title": "title_srtgb199", "child_ids": [111]},
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "child_ids": [112, 113],
                },
                "mediafile/112": {
                    "title": "title_srtgb123",
                    "parent_id": 111,
                    "access_group_ids": [7],
                },
                "mediafile/113": {
                    "title": "title_srtgb123",
                    "parent_id": 111,
                    "access_group_ids": [7],
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee", "access_group_ids": [7]},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("title") == "title_Xcdfgee"
        assert model.get("access_group_ids") == [7]
        assert model.get("inherited_access_group_ids") == [7]
        assert model.get("is_public") is False
        child = self.get_model("mediafile/112")
        assert child.get("access_group_ids") == [7]
        assert child.get("inherited_access_group_ids") == [7]
        assert child.get("is_public") is False
        child = self.get_model("mediafile/113")
        assert child.get("access_group_ids") == [7]
        assert child.get("inherited_access_group_ids") == [7]
        assert child.get("is_public") is False

    def test_update_parent_and_children_3(self) -> None:
        self.set_models(
            {
                "group/7": {"name": "group_LxAHErRs", "user_ids": []},
                "mediafile/110": {"title": "title_srtgb199", "child_ids": [111]},
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "child_ids": [112],
                },
                "mediafile/112": {
                    "title": "title_srtgb123",
                    "parent_id": 111,
                    "access_group_ids": [7],
                    "child_ids": [113],
                },
                "mediafile/113": {
                    "title": "title_srtgb123",
                    "parent_id": 112,
                    "access_group_ids": [7],
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee", "access_group_ids": [7]},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("title") == "title_Xcdfgee"
        assert model.get("access_group_ids") == [7]
        assert model.get("inherited_access_group_ids") == [7]
        assert model.get("is_public") is False
        child = self.get_model("mediafile/112")
        assert child.get("access_group_ids") == [7]
        assert child.get("inherited_access_group_ids") == [7]
        assert child.get("is_public") is False
        child = self.get_model("mediafile/113")
        assert child.get("access_group_ids") == [7]
        assert child.get("inherited_access_group_ids") == [7]
        assert child.get("is_public") is False

    def test_update_filename_error(self) -> None:
        self.set_models(
            {
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "filename": "testfile.txt",
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {"id": 110, "filename": "testfile.txt2"},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'filename'} properties", response.json["message"]
        )
