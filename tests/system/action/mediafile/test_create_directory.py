from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class MediafileCreateDirectoryActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "group/7": {
                "name": "group_LxAHErRs",
                "meeting_user_ids": [],
                "meeting_id": 1,
            },
        }

    def test_create_directory_correct(self) -> None:
        self.set_models(
            {
                "group/7": {
                    "name": "group_LxAHErRs",
                    "meeting_user_ids": [],
                    "meeting_id": 110,
                },
                "meeting/110": {
                    "name": "meeting110",
                    "is_active_in_organization_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
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

    def test_create_directory_organization_correct(self) -> None:
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": ONE_ORGANIZATION_FQID,
                "title": "title_Xcdfgee",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/1",
            {
                "title": "title_Xcdfgee",
                "access_group_ids": None,
                "is_directory": True,
                "inherited_access_group_ids": None,
                "is_public": True,
            },
        )

    def test_create_directory_parent(self) -> None:
        self.set_models(
            {
                "group/7": {
                    "name": "group_LxAHErRs",
                    "meeting_user_ids": [],
                    "meeting_id": 110,
                },
                "meeting/110": {
                    "name": "meeting110",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "owner_id": "meeting/110",
                    "is_directory": True,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
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
                    "meeting_user_ids": [],
                    "meeting_id": 110,
                },
                "group/8": {
                    "name": "group_sdfafd",
                    "meeting_user_ids": [],
                    "meeting_id": 110,
                },
                "meeting/110": {
                    "name": "meeting110",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "inherited_access_group_ids": [8],
                    "is_public": False,
                    "owner_id": "meeting/110",
                    "is_directory": True,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
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
                    "access_group_ids": [],
                    "inherited_access_group_ids": [],
                    "is_public": True,
                    "owner_id": "meeting/110",
                    "is_directory": True,
                },
                "meeting/110": {
                    "name": "meeting110",
                    "is_active_in_organization_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
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
                    "meeting_user_ids": [],
                    "meeting_id": 110,
                },
                "group/4": {
                    "name": "group_sdfafd",
                    "meeting_user_ids": [],
                    "meeting_id": 110,
                },
                "meeting/110": {
                    "name": "meeting110",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "inherited_access_group_ids": [2, 4],
                    "access_group_ids": [2, 4],
                    "owner_id": "meeting/110",
                    "is_directory": True,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
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
                    "meeting_user_ids": [],
                    "meeting_id": 110,
                },
                "group/6": {
                    "name": "group_sdfafd",
                    "meeting_user_ids": [],
                    "meeting_id": 110,
                },
                "meeting/110": {
                    "name": "meeting110",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "inherited_access_group_ids": [],
                    "access_group_ids": [],
                    "owner_id": "meeting/110",
                    "is_directory": True,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
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
                    "meeting_user_ids": [],
                    "meeting_id": 110,
                },
                "group/2": {
                    "name": "group_sdfafd",
                    "meeting_user_ids": [],
                    "meeting_id": 110,
                },
                "group/3": {
                    "name": "group_ghjeei",
                    "meeting_user_ids": [],
                    "meeting_id": 110,
                },
                "meeting/110": {
                    "name": "meeting110",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "inherited_access_group_ids": [1, 2],
                    "access_group_ids": [1, 2],
                    "owner_id": "meeting/110",
                    "is_directory": True,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
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
                    "meeting_user_ids": [],
                    "meeting_id": 110,
                },
                "group/2": {
                    "name": "group_sdfafd",
                    "meeting_user_ids": [],
                    "meeting_id": 110,
                },
                "group/3": {
                    "name": "group_ghjeei",
                    "meeting_user_ids": [],
                    "meeting_id": 110,
                },
                "meeting/110": {
                    "name": "meeting110",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "child_ids": [111],
                    "inherited_access_group_ids": [1, 2],
                    "is_public": False,
                    "access_group_ids": [1, 2],
                    "owner_id": "meeting/110",
                    "is_directory": True,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
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

    def test_create_directory_no_access_group_ids(self) -> None:
        self.set_models(
            {
                "meeting/110": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
                "title": "title_UoOFrRU3INADQbay",
                "parent_id": None,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/1")
        assert model.get("title") == "title_UoOFrRU3INADQbay"
        assert model.get("access_group_ids") is None
        assert model.get("inherited_access_group_ids") == []
        assert model.get("is_directory") is True
        assert model.get("is_public") is True

    def test_create_directory_parent_id_parent_not_directory(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "meeting_1",
                    "mediafile_ids": [7],
                    "is_active_in_organization_id": 1,
                },
                "mediafile/7": {"owner_id": "meeting/1"},
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/1",
                "title": "title_1",
                "parent_id": 7,
            },
        )
        self.assert_status_code(response, 400)
        assert "Parent is not a directory." in response.json["message"]

    def test_create_directory_parent_id_owner_mismatch(self) -> None:
        self.set_models(
            {
                "meeting/1": {"mediafile_ids": [7], "is_active_in_organization_id": 1},
                "meeting/2": {"is_active_in_organization_id": 1},
                "mediafile/7": {"owner_id": "meeting/1", "is_directory": True},
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/2",
                "title": "title_1",
                "parent_id": 7,
            },
        )
        self.assert_status_code(response, 400)
        assert "Owner and parent don't match." in response.json["message"]

    def test_create_directory_mix_meeting_and_orga(self) -> None:
        self.set_models(
            {
                "meeting/1": {"mediafile_ids": [7], "is_active_in_organization_id": 1},
                "mediafile/7": {"owner_id": "meeting/1", "is_directory": True},
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": ONE_ORGANIZATION_FQID,
                "title": "title_1",
                "parent_id": 7,
            },
        )
        self.assert_status_code(response, 400)
        assert "Owner and parent don't match." in response.json["message"]

    def test_create_directory_title_parent_id_unique(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "mediafile_ids": [6, 7],
                    "is_active_in_organization_id": 1,
                },
                "mediafile/6": {
                    "title": "parent_title_1",
                    "is_directory": True,
                    "owner_id": "meeting/1",
                    "child_ids": [7],
                },
                "mediafile/7": {
                    "title": "title_1",
                    "owner_id": "meeting/1",
                    "parent_id": 6,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/1",
                "title": "title_1",
                "parent_id": 6,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "File 'title_1' already exists in folder 'parent_title_1'."
            in response.json["message"]
        )

    def test_create_directory_owner_access_groups_dont_match(self) -> None:
        self.set_models(
            {
                "meeting/1": {"group_ids": [11], "is_active_in_organization_id": 1},
                "meeting/2": {"is_active_in_organization_id": 1},
                "group/11": {"meeting_id": 1},
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/2",
                "title": "title_1",
                "access_group_ids": [11],
            },
        )
        self.assert_status_code(response, 400)
        assert "Owner and access groups don't match." in response.json["message"]

    def test_create_directory_two_meetings(self) -> None:
        self.set_models(
            {
                "meeting/1": {"group_ids": [11], "is_active_in_organization_id": 1},
                "meeting/2": {"is_active_in_organization_id": 1},
                "group/11": {"meeting_id": 1},
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/2",
                "title": "title_1",
            },
        )
        self.assert_status_code(response, 200)

        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/1",
                "title": "title_1",
            },
        )
        self.assert_status_code(response, 200)

    def test_create_directory_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.create_directory",
            {
                "owner_id": "meeting/1",
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
            },
        )

    def test_create_directory_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.create_directory",
            {
                "owner_id": "meeting/1",
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
            },
            Permissions.Mediafile.CAN_MANAGE,
        )

    def test_create_directory_no_permissions_orga_owner(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.create_directory",
            {
                "owner_id": ONE_ORGANIZATION_FQID,
                "title": "title_Xcdfgee",
            },
        )

    def test_create_directory_permissions_orga_owner(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.create_directory",
            {
                "owner_id": ONE_ORGANIZATION_FQID,
                "title": "title_Xcdfgee",
            },
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
