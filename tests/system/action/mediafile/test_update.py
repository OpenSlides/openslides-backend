from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase


class MediafileUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "group/7": {"name": "group_LxAHErRs", "meeting_id": 1},
            "mediafile/111": {"title": "title_srtgb123", "owner_id": "meeting/1"},
            "meeting_mediafile/1111": {
                "mediafile_id": 111,
                "is_public": True,
                "meeting_id": 1,
            },
        }
        self.orga_permission_test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {"admin_group_id": 8},
            "group/7": {"name": "group_LxAHErRs", "meeting_id": 1},
            "group/8": {"name": "group_2", "meeting_id": 1},
            "mediafile/111": {
                "title": "title_srtgb123",
                "owner_id": ONE_ORGANIZATION_FQID,
            },
        }

    def test_update_correct(self) -> None:
        self.set_models(
            {
                "group/7": {"name": "group_LxAHErRs", "meeting_id": 1},
                "mediafile/111": {"title": "title_srtgb123", "owner_id": "meeting/1"},
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": True,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {
                "id": 111,
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/111", {"title": "title_Xcdfgee"})
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "meeting_id": 1,
                "access_group_ids": [7],
                "inherited_access_group_ids": [7],
                "is_public": False,
            },
        )

    def test_update_children(self) -> None:
        self.set_models(
            {
                "group/7": {
                    "name": "group_LxAHErRs",
                    "meeting_mediafile_inherited_access_group_ids": [1110],
                    "meeting_mediafile_access_group_ids": [1110],
                    "meeting_id": 1,
                },
                "mediafile/110": {"title": "title_ekxORNiV", "owner_id": "meeting/1"},
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "meeting_id": 1,
                    "is_public": False,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": True,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {
                "id": 110,
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/111", {"title": "title_srtgb123"})
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {"meeting_id": 1, "inherited_access_group_ids": [7], "is_public": False},
        )

    def test_update_parent(self) -> None:
        self.set_models(
            {
                "group/7": {"name": "group_LxAHErRs", "meeting_id": 1},
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "is_directory": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "is_public": True,
                    "meeting_id": 1,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": True,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {
                "id": 111,
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/111", {"title": "title_Xcdfgee"})
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "meeting_id": 1,
                "access_group_ids": [7],
                "inherited_access_group_ids": [7],
                "is_public": False,
            },
        )

    def test_update_parent_inherited_list(self) -> None:
        self.set_models(
            {
                "group/7": {"name": "group_LxAHErRs", "meeting_id": 1},
                "group/8": {
                    "name": "group_sdfafd",
                    "meeting_mediafile_inherited_access_group_ids": [1110],
                    "meeting_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "is_directory": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "meeting_id": 1,
                    "is_public": False,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": True,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {
                "id": 111,
                "meeting_id": 1,
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/111", {"title": "title_Xcdfgee"})
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "meeting_id": 1,
                "access_group_ids": [7],
                "inherited_access_group_ids": None,
                "is_public": False,
            },
        )

    def test_update_parent_case1(self) -> None:
        self.set_models(
            {
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "is_directory": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "meeting_id": 1,
                    "is_public": True,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "meeting_id": 1,
                    "is_public": True,
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {
                "id": 111,
                "meeting_id": 1,
                "title": "title_Xcdfgee",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "meeting_id": 1,
                "mediafile_id": 111,
                "access_group_ids": None,
                "inherited_access_group_ids": None,
                "is_public": True,
            },
        )

    def test_update_parent_case2(self) -> None:
        self.set_models(
            {
                "group/3": {
                    "meeting_mediafile_inherited_access_group_ids": [1110],
                    "meeting_mediafile_access_group_ids": [1110],
                    "meeting_id": 1,
                },
                "group/4": {
                    "name": "group_sdfafd",
                    "meeting_mediafile_inherited_access_group_ids": [1110],
                    "meeting_mediafile_access_group_ids": [1110],
                    "meeting_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "is_directory": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "meeting_id": 1,
                    "is_public": False,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": True,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {
                "id": 111,
                "meeting_id": 1,
                "title": "title_Xcdfgee",
                "access_group_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "access_group_ids": None,
                "inherited_access_group_ids": [3, 4],
                "is_public": False,
            },
        )

    def test_update_parent_case3(self) -> None:
        self.set_models(
            {
                "group/3": {"name": "group_LxAHErRs", "meeting_id": 1},
                "group/6": {"name": "group_sdfafd", "meeting_id": 1},
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "is_directory": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "meeting_id": 1,
                    "is_public": True,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": True,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {
                "id": 111,
                "title": "title_Xcdfgee",
                "access_group_ids": [3, 6],
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "access_group_ids": [3, 6],
                "inherited_access_group_ids": [3, 6],
                "is_public": False,
            },
        )

    def test_update_parent_case4(self) -> None:
        self.set_models(
            {
                "group/1": {
                    "name": "group_LxAHErRs",
                    "meeting_mediafile_inherited_access_group_ids": [1110],
                    "meeting_mediafile_access_group_ids": [1110],
                    "meeting_id": 1,
                },
                "group/2": {
                    "name": "group_sdfafd",
                    "meeting_mediafile_inherited_access_group_ids": [1110],
                    "meeting_mediafile_access_group_ids": [1110],
                    "meeting_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "is_directory": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "meeting_id": 1,
                    "is_public": False,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": True,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {
                "id": 111,
                "title": "title_Xcdfgee",
                "access_group_ids": [2, 3],
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "access_group_ids": [2, 3],
                "inherited_access_group_ids": [2],
                "is_public": False,
            },
        )

    def test_update_parent_case5(self) -> None:
        self.set_models(
            {
                "group/1": {
                    "name": "group_LxAHErRs",
                    "meeting_mediafile_inherited_access_group_ids": [1110],
                    "meeting_mediafile_access_group_ids": [1110],
                    "meeting_id": 1,
                },
                "group/2": {
                    "name": "group_sdfafd",
                    "meeting_mediafile_inherited_access_group_ids": [1110],
                    "meeting_mediafile_access_group_ids": [1110],
                    "meeting_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "is_directory": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "meeting_id": 1,
                    "is_public": False,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": True,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {
                "id": 111,
                "meeting_id": 1,
                "title": "title_Xcdfgee",
                "access_group_ids": [3],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "access_group_ids": [3],
                "inherited_access_group_ids": None,
                "is_public": False,
            },
        )

    def test_update_parent_inherited_true(self) -> None:
        self.set_models(
            {
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "is_directory": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "meeting_id": 1,
                    "is_public": False,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": True,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {
                "id": 111,
                "meeting_id": 1,
                "title": "title_Xcdfgee",
                "access_group_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "access_group_ids": None,
                "inherited_access_group_ids": None,
                "is_public": False,
            },
        )

    def test_update_wrong_id(self) -> None:
        self.create_model(
            "mediafile/111",
            {"owner_id": ONE_ORGANIZATION_FQID, "title": "title_srtgb123"},
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
                "group/7": {
                    "name": "group_LxAHErRs",
                    "meeting_mediafile_access_group_ids": [1112],
                    "meeting_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "is_directory": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
                "mediafile/112": {
                    "title": "title_srtgb123",
                    "parent_id": 111,
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "is_public": True,
                    "meeting_id": 1,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": True,
                    "meeting_id": 1,
                },
                "meeting_mediafile/1112": {
                    "mediafile_id": 112,
                    "is_public": True,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {
                "id": 111,
                "meeting_id": 1,
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "access_group_ids": [7],
                "inherited_access_group_ids": [7],
                "is_public": False,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1112",
            {
                "access_group_ids": [7],
                "inherited_access_group_ids": [7],
                "is_public": False,
            },
        )

    def test_update_parent_and_children_2(self) -> None:
        self.set_models(
            {
                "group/7": {"name": "group_LxAHErRs", "meeting_id": 1},
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "is_directory": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "is_directory": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/112": {
                    "title": "title_srtgb123",
                    "parent_id": 111,
                    "owner_id": "meeting/1",
                },
                "mediafile/113": {
                    "title": "title_srtgb123",
                    "parent_id": 111,
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "meeting_id": 1,
                    "is_public": True,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "meeting_id": 1,
                    "is_public": True,
                },
                "meeting_mediafile/1112": {
                    "mediafile_id": 112,
                    "meeting_id": 1,
                    "is_public": True,
                },
                "meeting_mediafile/1113": {
                    "mediafile_id": 113,
                    "meeting_id": 1,
                    "is_public": True,
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {
                "id": 110,
                "meeting_id": 1,
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/7",
            {
                "meeting_mediafile_access_group_ids": [1110],
                "meeting_mediafile_inherited_access_group_ids": [
                    1110,
                    1111,
                    1112,
                    1113,
                ],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1110",
            {
                "is_public": False,
                "access_group_ids": [7],
                "inherited_access_group_ids": [7],
            },
        )
        mediafiles_to_check = (
            "meeting_mediafile/1111",
            "meeting_mediafile/1112",
            "meeting_mediafile/1113",
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
                "group/7": {
                    "name": "group_LxAHErRs",
                    "meeting_mediafile_access_group_ids": [1112, 1113],
                    "meeting_id": 1,
                },
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "is_directory": True,
                    "owner_id": "meeting/1",
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "parent_id": 110,
                    "owner_id": "meeting/1",
                },
                "mediafile/112": {
                    "title": "title_srtgb123",
                    "parent_id": 111,
                    "owner_id": "meeting/1",
                },
                "mediafile/113": {
                    "title": "title_srtgb123",
                    "parent_id": 112,
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "is_public": True,
                    "meeting_id": 1,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": True,
                    "meeting_id": 1,
                },
                "meeting_mediafile/1112": {
                    "mediafile_id": 112,
                    "is_public": True,
                    "meeting_id": 1,
                },
                "meeting_mediafile/1113": {
                    "mediafile_id": 113,
                    "is_public": True,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {
                "id": 111,
                "meeting_id": 1,
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
            },
        )
        self.assert_status_code(response, 200)
        mediafiles_to_check = (
            "meeting_mediafile/1111",
            "meeting_mediafile/1112",
            "meeting_mediafile/1113",
        )
        for mediafile in mediafiles_to_check:
            self.assert_model_exists(
                mediafile,
                {
                    "is_public": False,
                    "access_group_ids": [7],
                    "inherited_access_group_ids": [7],
                },
            )

    def test_update_filename_error(self) -> None:
        self.set_models(
            {
                "mediafile/110": {
                    "title": "title_srtgb199",
                    "filename": "testfile.txt",
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "is_public": True,
                    "meeting_id": 1,
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

    def test_update_title_with_orga_owner_meeting_id_none(self) -> None:
        self.set_models(self.orga_permission_test_models)
        response = self.request(
            "mediafile.update", {"id": 111, "title": "blob.txt", "meeting_id": None}
        )
        self.assert_status_code(response, 400)
        self.assertIn("data.meeting_id must be integer", response.json["message"])

    def test_update_access_group_with_orga_owner(self) -> None:
        self.set_models(self.orga_permission_test_models)
        response = self.request(
            "mediafile.update", {"id": 111, "meeting_id": 1, "access_group_ids": [7]}
        )
        self.assert_status_code(response, 400)
        assert (
            "access_group_ids is not allowed in organization mediafiles."
            == response.json["message"]
        )

    def test_update_access_group_on_published_orga_file(self) -> None:
        self.set_models(self.orga_permission_test_models)
        self.set_models(
            {
                "mediafile/111": {
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID
                }
            }
        )
        response = self.request(
            "mediafile.update", {"id": 111, "meeting_id": 1, "access_group_ids": [7]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "mediafile_id": 111,
                "meeting_id": 1,
                "access_group_ids": [7],
                "inherited_access_group_ids": [7],
            },
        )

    def test_update_access_group_on_implicitly_published_orga_file_implicit_parent_meeting_data(
        self,
    ) -> None:
        self.set_models(self.orga_permission_test_models)
        self.set_models(
            {
                "mediafile/111": {
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID
                },
                "mediafile/112": {
                    "parent_id": 111,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "title": "title_blabla",
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
                "mediafile/113": {
                    "parent_id": 112,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "title": "title_blabliblub",
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
            }
        )
        response = self.request(
            "mediafile.update", {"id": 112, "meeting_id": 1, "access_group_ids": [7, 8]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "mediafile_id": 112,
                "meeting_id": 1,
                "access_group_ids": [7, 8],
                "inherited_access_group_ids": [8],
            },
        )
        self.assert_model_not_exists("meeting_mediafile/2")

    def test_update_access_group_on_implicitly_published_orga_file_explicit_parent_meeting_data(
        self,
    ) -> None:
        self.set_models(self.orga_permission_test_models)
        self.set_models(
            {
                "group/8": {
                    "meeting_mediafile_access_group_ids": [1111],
                    "meeting_mediafile_inherited_access_group_ids": [1111],
                },
                "mediafile/111": {
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "child_ids": [112],
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": True,
                    "meeting_id": 1,
                },
                "mediafile/112": {
                    "parent_id": 111,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "title": "title_blabla",
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
            }
        )
        response = self.request(
            "mediafile.update", {"id": 112, "meeting_id": 1, "access_group_ids": [7, 8]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1112",
            {
                "mediafile_id": 112,
                "meeting_id": 1,
                "access_group_ids": [7, 8],
                "inherited_access_group_ids": [8],
            },
        )

    def test_update_access_group_on_implicitly_published_orga_file_explicit_grandparent_meeting_data(
        self,
    ) -> None:
        self.set_models(self.orga_permission_test_models)
        self.set_models(
            {
                "group/7": {"meeting_mediafile_access_group_ids": [1]},
                "group/8": {
                    "meeting_mediafile_access_group_ids": [1],
                    "meeting_mediafile_inherited_access_group_ids": [1],
                },
                "mediafile/111": {
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID
                },
                "mediafile/112": {
                    "parent_id": 111,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "title": "title_blabla",
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
                "mediafile/113": {
                    "parent_id": 112,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "title": "title_blabliblub",
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
                "mediafile/114": {
                    "parent_id": 113,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "title": "title_blabliblub",
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
                "meeting_mediafile/1": {
                    "mediafile_id": 112,
                    "meeting_id": 1,
                    "is_public": True,
                },
            }
        )
        response = self.request(
            "mediafile.update", {"id": 114, "meeting_id": 1, "access_group_ids": [7, 8]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/2",
            {
                "mediafile_id": 114,
                "meeting_id": 1,
                "access_group_ids": [7, 8],
                "inherited_access_group_ids": [8],
            },
        )
        self.assert_model_not_exists("meeting_mediafile/3")

    def test_update_access_group_on_published_root_mediafile(self) -> None:
        self.set_models(self.orga_permission_test_models)
        self.set_models(
            {
                "group/7": {"meeting_mediafile_access_group_ids": [1]},
                "group/8": {
                    "meeting_mediafile_access_group_ids": [1],
                    "meeting_mediafile_inherited_access_group_ids": [1],
                },
                "group/9": {"name": "group_3", "meeting_id": 1},
                "mediafile/111": {
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID
                },
                "mediafile/112": {
                    "parent_id": 111,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "title": "title_blabla",
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
                "mediafile/113": {
                    "parent_id": 112,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "title": "title_blabliblub",
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
                "mediafile/114": {
                    "parent_id": 113,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "title": "title_blabliblub",
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
                "meeting_mediafile/1": {
                    "mediafile_id": 113,
                    "is_public": True,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.update", {"id": 111, "meeting_id": 1, "access_group_ids": [7, 9]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "mediafile_id": 113,
                "meeting_id": 1,
                "access_group_ids": [7, 8],
                "inherited_access_group_ids": [7],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/2",
            {
                "mediafile_id": 111,
                "meeting_id": 1,
                "access_group_ids": [7, 9],
                "inherited_access_group_ids": [7, 9],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/3",
            {
                "mediafile_id": 112,
                "meeting_id": 1,
                "access_group_ids": None,
                "inherited_access_group_ids": [7, 9],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/4",
            {
                "mediafile_id": 114,
                "meeting_id": 1,
                "access_group_ids": None,
                "inherited_access_group_ids": [7],
            },
        )

    def test_update_access_group_different_owner(self) -> None:
        self.create_meeting(4)
        self.permission_test_models["group/7"]["meeting_id"] = 4
        self.set_models(self.permission_test_models)
        response = self.request(
            "mediafile.update",
            {"id": 111, "meeting_id": 1, "access_group_ids": [7]},
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
                "organization/2": {
                    "name": "irresponsible org",
                    "default_language": "en",
                    "theme_id": 2,
                },
                "theme/2": {"name": "OpenSlides Organization"},
                "mediafile/7": {"token": "token_1", "owner_id": ONE_ORGANIZATION_FQID},
                "mediafile/8": {"token": "token_2", "owner_id": "organization/2"},
            }
        )
        response = self.request("mediafile.update", {"id": 8, "token": "token_1"})
        self.assert_status_code(response, 400)
        assert "Token 'token_1' is not unique."

    def test_update_token_payload_old_token(self) -> None:
        self.set_models(
            {"mediafile/7": {"token": "token_1", "owner_id": ONE_ORGANIZATION_FQID}}
        )
        response = self.request("mediafile.update", {"id": 7, "token": "token_1"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/7", {"token": "token_1"})

    def test_update_title_parent_id_unique(self) -> None:
        self.set_models(
            {
                "mediafile/6": {"title": "parent_title_1", "owner_id": "meeting/1"},
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
                "meeting_mediafile/16": {
                    "mediafile_id": 6,
                    "is_public": True,
                    "meeting_id": 1,
                },
                "meeting_mediafile/17": {
                    "mediafile_id": 7,
                    "is_public": True,
                    "meeting_id": 1,
                },
                "meeting_mediafile/18": {
                    "mediafile_id": 8,
                    "is_public": True,
                    "meeting_id": 1,
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
            {
                "id": 111,
                "meeting_id": 1,
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
            },
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.update",
            {
                "id": 111,
                "meeting_id": 1,
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
            },
            Permissions.Mediafile.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "mediafile.update",
            {
                "id": 111,
                "meeting_id": 1,
                "title": "title_Xcdfgee",
                "access_group_ids": [7],
            },
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

    def test_update_meeting_permissions_orga_owner_on_published_file_error(
        self,
    ) -> None:
        self.orga_permission_test_models["mediafile/111"][
            "published_to_meetings_in_organization_id"
        ] = ONE_ORGANIZATION_ID
        self.base_permission_test(
            self.orga_permission_test_models,
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee"},
            Permissions.Mediafile.CAN_MANAGE,
            fail=True,
        )

    def test_update_meeting_permissions_orga_owner_on_published_file(self) -> None:
        self.orga_permission_test_models["mediafile/111"][
            "published_to_meetings_in_organization_id"
        ] = ONE_ORGANIZATION_ID
        self.base_permission_test(
            self.orga_permission_test_models,
            "mediafile.update",
            {"id": 111, "meeting_id": 1, "access_group_ids": [7]},
            Permissions.Mediafile.CAN_MANAGE,
        )
