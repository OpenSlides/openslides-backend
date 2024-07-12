from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class MediafileUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {"name": "meeting_1", "is_active_in_organization_id": 1},
            "group/7": {
                "name": "group_LxAHErRs",
                "meeting_user_ids": [],
                "meeting_id": 1,
            },
            "mediafile/111": {"title": "title_srtgb123", "owner_id": "meeting/1"},
        }

    def test_update_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/7": {
                    "name": "group_LxAHErRs",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "mediafile/111": {"title": "title_srtgb123", "owner_id": "meeting/1"},
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
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/7": {
                    "name": "group_LxAHErRs",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "mediafile/110": {
                    "title": "title_ekxORNiV",
                    "child_ids": [111],
                    "is_public": False,
                    "inherited_access_group_ids": [7],
                    "access_group_ids": [7],
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
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
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/7": {
                    "name": "group_LxAHErRs",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "is_directory": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
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

    def test_update_parent_inherited_list(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/7": {
                    "name": "group_LxAHErRs",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "group/8": {
                    "name": "group_sdfafd",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "is_directory": True,
                    "inherited_access_group_ids": [8],
                    "is_public": False,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
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
        assert model.get("inherited_access_group_ids") == []
        assert model.get("is_public") is False

    def test_update_parent_case1(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "is_directory": True,
                    "access_group_ids": [],
                    "inherited_access_group_ids": [],
                    "is_public": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
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
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/2": {
                    "name": "group_LxAHErRs",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "group/4": {
                    "name": "group_sdfafd",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "is_directory": True,
                    "inherited_access_group_ids": [2, 4],
                    "access_group_ids": [2, 4],
                    "is_public": False,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
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
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/3": {
                    "name": "group_LxAHErRs",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "group/6": {
                    "name": "group_sdfafd",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "is_directory": True,
                    "inherited_access_group_ids": [],
                    "access_group_ids": [],
                    "is_public": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
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
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/1": {
                    "name": "group_LxAHErRs",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "group/2": {
                    "name": "group_sdfafd",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "group/3": {
                    "name": "group_ghjeei",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "is_directory": True,
                    "inherited_access_group_ids": [1, 2],
                    "access_group_ids": [1, 2],
                    "is_public": False,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
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
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/1": {
                    "name": "group_LxAHErRs",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "group/2": {
                    "name": "group_sdfafd",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "group/3": {
                    "name": "group_ghjeei",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "is_directory": True,
                    "inherited_access_group_ids": [1, 2],
                    "access_group_ids": [1, 2],
                    "is_public": False,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
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
                "meeting/1": {"is_active_in_organization_id": 1},
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "is_directory": True,
                    "inherited_access_group_ids": [],
                    "access_group_ids": [],
                    "is_public": False,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
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
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/7": {
                    "name": "group_LxAHErRs",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "is_directory": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "child_ids": [112],
                    "owner_id": "meeting/1",
                },
                "mediafile/112": {
                    "title": "title_srtgb123",
                    "parent_id": 111,
                    "access_group_ids": [7],
                    "owner_id": "meeting/1",
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
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/7": {
                    "name": "group_LxAHErRs",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "is_directory": True,
                    "is_public": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "child_ids": [112, 113],
                    "is_directory": True,
                    "is_public": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/112": {
                    "title": "title_srtgb123",
                    "parent_id": 111,
                    "is_public": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/113": {
                    "title": "title_srtgb123",
                    "parent_id": 111,
                    "is_public": True,
                    "owner_id": "meeting/1",
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {"id": 110, "title": "title_Xcdfgee", "access_group_ids": [7]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/7",
            {
                "mediafile_access_group_ids": [110],
                "mediafile_inherited_access_group_ids": [110, 111, 112, 113],
            },
        )
        self.assert_model_exists(
            "mediafile/110",
            {
                "is_public": False,
                "access_group_ids": [7],
                "inherited_access_group_ids": [7],
            },
        )
        mediafiles_to_check = (
            "mediafile/111",
            "mediafile/112",
            "mediafile/113",
        )
        for mediafile in mediafiles_to_check:
            self.assert_model_exists(
                mediafile,
                {
                    "is_public": False,
                    "access_group_ids": None,
                    "inherited_access_group_ids": [7],
                },
            )

    def test_update_parent_and_children_3(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/7": {
                    "name": "group_LxAHErRs",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "is_directory": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "child_ids": [112],
                    "owner_id": "meeting/1",
                },
                "mediafile/112": {
                    "title": "title_srtgb123",
                    "parent_id": 111,
                    "access_group_ids": [7],
                    "child_ids": [113],
                    "owner_id": "meeting/1",
                },
                "mediafile/113": {
                    "title": "title_srtgb123",
                    "parent_id": 112,
                    "access_group_ids": [7],
                    "owner_id": "meeting/1",
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
                "meeting/1": {"is_active_in_organization_id": 1},
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "filename": "testfile.txt",
                    "owner_id": "meeting/1",
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

    def test_update_access_group_with_orga_owner(self) -> None:
        self.permission_test_models["mediafile/111"]["owner_id"] = ONE_ORGANIZATION_FQID
        self.set_models(self.permission_test_models)
        response = self.request(
            "mediafile.update", {"id": 111, "access_group_ids": [7]}
        )
        self.assert_status_code(response, 400)
        assert (
            "access_group_ids is not allowed in organization mediafiles."
            == response.json["message"]
        )

    def test_update_access_group_different_owner(self) -> None:
        self.permission_test_models["group/7"]["meeting_id"] = 2
        self.set_models(self.permission_test_models)
        response = self.request(
            "mediafile.update",
            {"id": 111, "access_group_ids": [7]},
        )
        self.assert_status_code(response, 400)
        assert "Owner and access groups don't match." in response.json["message"]

    def test_update_token_payload_check_orga_owner(self) -> None:
        self.set_models(self.permission_test_models)
        response = self.request(
            "mediafile.update",
            {"id": 111, "token": "test"},
        )
        self.assert_status_code(response, 400)
        assert "token is not allowed in meeting mediafiles." in response.json["message"]

    def test_update_token_payload_token_unique(self) -> None:
        self.set_models(
            {
                "mediafile/7": {"token": "token_1", "owner_id": ONE_ORGANIZATION_FQID},
                "mediafile/8": {"token": "token_2", "owner_id": "organization/2"},
            }
        )
        response = self.request(
            "mediafile.update",
            {"id": 8, "token": "token_1"},
        )
        self.assert_status_code(response, 400)
        assert "Token 'token_1' is not unique."

    def test_update_token_payload_old_token(self) -> None:
        self.set_models(
            {
                "mediafile/7": {"token": "token_1", "owner_id": ONE_ORGANIZATION_FQID},
            }
        )
        response = self.request(
            "mediafile.update",
            {"id": 7, "token": "token_1"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/7", {"token": "token_1"})

    def test_update_title_parent_id_unique(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "is_active_in_organization_id": 1,
                    "mediafile_ids": [6, 7, 8],
                },
                "mediafile/6": {
                    "title": "parent_title_1",
                    "child_ids": [7, 8],
                    "owner_id": "meeting/1",
                },
                "mediafile/7": {
                    "title": "title_1",
                    "parent_id": 6,
                    "owner_id": "meeting/1",
                },
                "mediafile/8": {
                    "title": "title_2",
                    "parent_id": 6,
                    "owner_id": "meeting/1",
                },
            }
        )
        response = self.request("mediafile.update", {"id": 8, "title": "title_1"})
        self.assert_status_code(response, 400)
        assert (
            "File 'title_1' already exists in folder 'parent_title_1'."
            in response.json["message"]
        )

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee", "access_group_ids": [7]},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee", "access_group_ids": [7]},
            Permissions.Mediafile.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee", "access_group_ids": [7]},
        )

    def test_update_no_permissions_orga_owner(self) -> None:
        self.permission_test_models["mediafile/111"]["owner_id"] = ONE_ORGANIZATION_FQID
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee"},
        )

    def test_update_permissions_orga_owner(self) -> None:
        self.permission_test_models["mediafile/111"]["owner_id"] = ONE_ORGANIZATION_FQID
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee"},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
