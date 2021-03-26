from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MediafileCreateDirectoryActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model = {
            "group/7": {
                "name": "group_LxAHErRs",
                "user_ids": [],
                "meeting_id": 1,
            },
        }

    def test_create_directory_correct(self) -> None:
        self.set_models(
            {
                "group/7": {
                    "name": "group_LxAHErRs",
                    "user_ids": [],
                    "meeting_id": 110,
                },
                "meeting/110": {"name": "meeting110"},
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "meeting_id": 110,
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/1")
        assert model.get("title") == "title_Xcdfgee"
        assert model.get("access_group_ids") == [7]
        assert model.get("is_directory") is True
        assert model.get("inherited_access_group_ids") == [7]
        assert model.get("is_public") is False

    def test_create_directory_parent(self) -> None:
        self.set_models(
            {
                "group/7": {
                    "name": "group_LxAHErRs",
                    "user_ids": [],
                    "meeting_id": 110,
                },
                "meeting/110": {"name": "meeting110"},
                "mediafile/110": {"title": "title_srtgb199", "meeting_id": 110},
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "meeting_id": 110,
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
                "parent_id": 110,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("title") == "title_Xcdfgee"
        assert model.get("access_group_ids") == [7]
        assert model.get("inherited_access_group_ids") == [7]
        assert model.get("is_public") is False

    def test_create_directory_parent_inherited_list(self) -> None:
        self.set_models(
            {
                "group/7": {
                    "name": "group_LxAHErRs",
                    "user_ids": [],
                    "meeting_id": 110,
                },
                "group/8": {"name": "group_sdfafd", "user_ids": [], "meeting_id": 110},
                "meeting/110": {"name": "meeting110"},
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "inherited_access_group_ids": [8],
                    "is_public": False,
                    "meeting_id": 110,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "meeting_id": 110,
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
                "parent_id": 110,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("title") == "title_Xcdfgee"
        assert model.get("access_group_ids") == [7]
        assert model.get("inherited_access_group_ids") == []
        assert model.get("is_public") is False

    def test_create_directory_parent_case1(self) -> None:
        self.set_models(
            {
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "access_group_ids": [],
                    "inherited_access_group_ids": [],
                    "is_public": True,
                    "meeting_id": 110,
                },
                "meeting/110": {"name": "meeting110"},
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "meeting_id": 110,
                "title": "title_Xcdfgee",
                "access_group_ids": [],
                "parent_id": 110,
            },
        )
        self.assert_status_code(response, 200)
        model_child = self.get_model("mediafile/111")
        assert model_child.get("access_group_ids") == []
        assert model_child.get("inherited_access_group_ids") == []
        assert model_child.get("is_public") is True

    def test_create_directory_parent_case2(self) -> None:
        self.set_models(
            {
                "group/2": {
                    "name": "group_LxAHErRs",
                    "user_ids": [],
                    "meeting_id": 110,
                },
                "group/4": {"name": "group_sdfafd", "user_ids": [], "meeting_id": 110},
                "meeting/110": {"name": "meeting110"},
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "inherited_access_group_ids": [2, 4],
                    "access_group_ids": [2, 4],
                    "meeting_id": 110,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "meeting_id": 110,
                "title": "title_Xcdfgee",
                "access_group_ids": [],
                "parent_id": 110,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("access_group_ids") == []
        assert model.get("inherited_access_group_ids") == [2, 4]
        assert model.get("is_public") is False

    def test_create_directory_parent_case3(self) -> None:
        self.set_models(
            {
                "group/3": {
                    "name": "group_LxAHErRs",
                    "user_ids": [],
                    "meeting_id": 110,
                },
                "group/6": {"name": "group_sdfafd", "user_ids": [], "meeting_id": 110},
                "meeting/110": {"name": "meeting110"},
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "inherited_access_group_ids": [],
                    "access_group_ids": [],
                    "meeting_id": 110,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "meeting_id": 110,
                "title": "title_Xcdfgee",
                "access_group_ids": [3, 6],
                "parent_id": 110,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("access_group_ids") == [3, 6]
        assert model.get("inherited_access_group_ids") == [3, 6]
        assert model.get("is_public") is False

    def test_create_directory_parent_case4(self) -> None:
        self.set_models(
            {
                "group/1": {
                    "name": "group_LxAHErRs",
                    "user_ids": [],
                    "meeting_id": 110,
                },
                "group/2": {"name": "group_sdfafd", "user_ids": [], "meeting_id": 110},
                "group/3": {"name": "group_ghjeei", "user_ids": [], "meeting_id": 110},
                "meeting/110": {"name": "meeting110"},
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "inherited_access_group_ids": [1, 2],
                    "access_group_ids": [1, 2],
                    "meeting_id": 110,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "meeting_id": 110,
                "title": "title_Xcdfgee",
                "access_group_ids": [2, 3],
                "parent_id": 110,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("access_group_ids") == [2, 3]
        assert model.get("inherited_access_group_ids") == [2]
        assert model.get("is_public") is False

    def test_create_directory_parent_case5(self) -> None:
        self.set_models(
            {
                "group/1": {
                    "name": "group_LxAHErRs",
                    "user_ids": [],
                    "meeting_id": 110,
                },
                "group/2": {"name": "group_sdfafd", "user_ids": [], "meeting_id": 110},
                "group/3": {"name": "group_ghjeei", "user_ids": [], "meeting_id": 110},
                "meeting/110": {"name": "meeting110"},
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "inherited_access_group_ids": [1, 2],
                    "is_public": False,
                    "access_group_ids": [1, 2],
                    "meeting_id": 110,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "meeting_id": 110,
                "title": "title_Xcdfgee",
                "access_group_ids": [3],
                "parent_id": 110,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/111")
        assert model.get("access_group_ids") == [3]
        assert model.get("inherited_access_group_ids") == []
        assert model.get("is_public") is False

    def test_create_dictionary_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "mediafile.create_directory",
            {
                "meeting_id": 1,
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
            },
        )

    def test_create_dictionary_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "mediafile.create_directory",
            {
                "meeting_id": 1,
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
            },
            Permissions.Mediafile.CAN_MANAGE,
        )
