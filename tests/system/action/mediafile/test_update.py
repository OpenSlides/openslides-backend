from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class MediafileUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "mediafile/111": {"title": "title_srtgb123", "owner_id": "meeting/1"},
            "meeting_mediafile/1111": {
                "mediafile_id": 111,
                "is_public": True,
                "meeting_id": 1,
            },
        }
        self.orga_permission_test_models: dict[str, dict[str, Any]] = {
            "mediafile/111": {
                "title": "title_srtgb123",
                "owner_id": ONE_ORGANIZATION_FQID,
            },
        }

    def test_update_correct(self) -> None:
        self.create_mediafile(111, 1)
        self.set_models(
            {
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
                "access_group_ids": [3],
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/111", {"title": "title_Xcdfgee"})
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "meeting_id": 1,
                "access_group_ids": [3],
                "inherited_access_group_ids": [3],
                "is_public": False,
            },
        )

    def test_update_children(self) -> None:
        self.create_mediafile(110, 1, is_directory=True)
        self.create_mediafile(111, 1, parent_id=110)
        self.set_models(
            {
                "group/3": {
                    "meeting_mediafile_inherited_access_group_ids": [1110],
                    "meeting_mediafile_access_group_ids": [1110],
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "meeting_id": 1,
                    "is_public": False,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": False,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.update",
            {
                "id": 110,
                "title": "title_Xcdfgee",
                "access_group_ids": [3],
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/111", {"title": "file_111"})
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {"meeting_id": 1, "inherited_access_group_ids": [3], "is_public": False},
        )

    def test_update_parent(self) -> None:
        self.create_mediafile(110, 1, is_directory=True)
        self.create_mediafile(111, 1, parent_id=110)
        self.set_models(
            {
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
                "access_group_ids": [3],
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/111", {"title": "title_Xcdfgee"})
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "meeting_id": 1,
                "access_group_ids": [3],
                "inherited_access_group_ids": [3],
                "is_public": False,
            },
        )

    def test_update_parent_inherited_list(self) -> None:
        self.create_mediafile(110, 1, is_directory=True)
        self.create_mediafile(111, 1, parent_id=110)
        self.set_models(
            {
                "group/2": {
                    "meeting_mediafile_access_group_ids": [1110],
                    "meeting_mediafile_inherited_access_group_ids": [1110],
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "meeting_id": 1,
                    "is_public": False,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": False,
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
        self.assert_model_exists("mediafile/111", {"title": "title_Xcdfgee"})
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "meeting_id": 1,
                "access_group_ids": [3],
                "inherited_access_group_ids": None,
                "is_public": False,
            },
        )

    def test_update_parent_case1(self) -> None:
        self.create_mediafile(110, 1, is_directory=True)
        self.create_mediafile(111, 1, parent_id=110)
        self.set_models(
            {
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
                "access_group_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/111", {"title": "title_Xcdfgee"})
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
        self.create_mediafile(110, 1, is_directory=True)
        self.create_mediafile(111, 1, parent_id=110)
        self.set_models(
            {
                "group/3": {
                    "meeting_mediafile_inherited_access_group_ids": [1110],
                    "meeting_mediafile_access_group_ids": [1110],
                },
                "group/1": {
                    "meeting_mediafile_inherited_access_group_ids": [1110],
                    "meeting_mediafile_access_group_ids": [1110],
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "meeting_id": 1,
                    "is_public": False,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": False,
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
                "inherited_access_group_ids": [1, 3],
                "is_public": False,
            },
        )

    def test_update_parent_case3(self) -> None:
        self.create_mediafile(110, 1, is_directory=True)
        self.create_mediafile(111, 1, parent_id=110)
        self.set_models(
            {
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
                "access_group_ids": [3, 1],
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "access_group_ids": [1, 3],
                "inherited_access_group_ids": [1, 3],
                "is_public": False,
            },
        )

    def test_update_parent_case4(self) -> None:
        self.create_mediafile(110, 1, is_directory=True)
        self.create_mediafile(111, 1, parent_id=110)
        self.set_models(
            {
                "group/1": {
                    "meeting_mediafile_inherited_access_group_ids": [1110],
                    "meeting_mediafile_access_group_ids": [1110],
                },
                "group/2": {
                    "meeting_mediafile_inherited_access_group_ids": [1110],
                    "meeting_mediafile_access_group_ids": [1110],
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "meeting_id": 1,
                    "is_public": False,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": False,
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
        self.create_mediafile(110, 1, is_directory=True)
        self.create_mediafile(111, 1, parent_id=110)
        self.set_models(
            {
                "group/1": {
                    "meeting_mediafile_inherited_access_group_ids": [1110],
                    "meeting_mediafile_access_group_ids": [1110],
                },
                "group/2": {
                    "meeting_mediafile_inherited_access_group_ids": [1110],
                    "meeting_mediafile_access_group_ids": [1110],
                },
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "meeting_id": 1,
                    "is_public": False,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": False,
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
        self.create_mediafile(110, 1, is_directory=True)
        self.create_mediafile(111, 1, parent_id=110)
        self.set_models(
            {
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "meeting_id": 1,
                    "is_public": False,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": False,
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
        self.create_mediafile(111)
        response = self.request(
            "mediafile.update", {"id": 112, "title": "title_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("mediafile/111")
        assert model.get("title") == "file_111"

    def test_update_parent_and_children(self) -> None:
        self.create_mediafile(110, 1, is_directory=True)
        self.create_mediafile(111, 1, is_directory=True, parent_id=110)
        self.create_mediafile(112, 1, parent_id=111)
        self.set_models(
            {
                "group/3": {"meeting_mediafile_access_group_ids": [1112]},
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "is_public": True,
                    "meeting_id": 1,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": False,
                    "meeting_id": 1,
                },
                "meeting_mediafile/1112": {
                    "mediafile_id": 112,
                    "is_public": False,
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
                "inherited_access_group_ids": [3],
                "is_public": False,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1112",
            {
                "access_group_ids": [3],
                "inherited_access_group_ids": [3],
                "is_public": False,
            },
        )

    def test_update_parent_and_children_2(self) -> None:
        self.create_mediafile(110, 1, is_directory=True)
        self.create_mediafile(111, 1, is_directory=True, parent_id=110)
        self.create_mediafile(112, 1, parent_id=111)
        self.create_mediafile(113, 1, parent_id=111)
        self.set_models(
            {
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
                "access_group_ids": [3],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/3",
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
                "access_group_ids": [3],
                "inherited_access_group_ids": [3],
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
                    "inherited_access_group_ids": [3],
                },
            )

    def test_update_parent_and_children_3(self) -> None:
        self.create_mediafile(110, 1, is_directory=True)
        self.create_mediafile(111, 1, is_directory=True, parent_id=110)
        self.create_mediafile(112, 1, is_directory=True, parent_id=111)
        self.create_mediafile(113, 1, parent_id=112)
        self.set_models(
            {
                "group/3": {"meeting_mediafile_access_group_ids": [1112, 1113]},
                "meeting_mediafile/1110": {
                    "mediafile_id": 110,
                    "is_public": True,
                    "meeting_id": 1,
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": False,
                    "meeting_id": 1,
                },
                "meeting_mediafile/1112": {
                    "mediafile_id": 112,
                    "is_public": False,
                    "meeting_id": 1,
                },
                "meeting_mediafile/1113": {
                    "mediafile_id": 113,
                    "is_public": False,
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
                    "access_group_ids": [3],
                    "inherited_access_group_ids": [3],
                },
            )

    def test_update_filename_error(self) -> None:
        self.create_mediafile(110, 1)
        self.set_models(
            {
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
        self.create_mediafile(111)
        response = self.request(
            "mediafile.update", {"id": 111, "meeting_id": 1, "access_group_ids": [3]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "mediafile_id": 111,
                "meeting_id": 1,
                "access_group_ids": [3],
                "inherited_access_group_ids": [3],
            },
        )

    def test_update_access_group_on_implicitly_published_orga_file_implicit_parent_meeting_data(
        self,
    ) -> None:
        self.create_mediafile(111, is_directory=True)
        self.create_mediafile(112, is_directory=True, parent_id=111)
        self.create_mediafile(113, parent_id=112)
        response = self.request(
            "mediafile.update", {"id": 112, "meeting_id": 1, "access_group_ids": [2, 3]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "mediafile_id": 112,
                "meeting_id": 1,
                "access_group_ids": [2, 3],
                "inherited_access_group_ids": [2],
            },
        )
        self.assert_model_not_exists("meeting_mediafile/2")

    def test_update_access_group_on_implicitly_published_orga_file_explicit_parent_meeting_data(
        self,
    ) -> None:
        self.create_mediafile(111, is_directory=True)
        self.create_mediafile(112, parent_id=111)
        self.set_models(
            {
                "group/2": {
                    "meeting_mediafile_access_group_ids": [1111],
                    "meeting_mediafile_inherited_access_group_ids": [1111],
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": False,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.update", {"id": 112, "meeting_id": 1, "access_group_ids": [2, 3]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1112",
            {
                "mediafile_id": 112,
                "meeting_id": 1,
                "access_group_ids": [2, 3],
                "inherited_access_group_ids": [2],
            },
        )

    def test_update_access_group_on_implicitly_published_orga_file_explicit_grandparent_meeting_data(
        self,
    ) -> None:
        self.create_mediafile(111, is_directory=True)
        self.create_mediafile(112, is_directory=True, parent_id=111)
        self.create_mediafile(113, is_directory=True, parent_id=112)
        self.create_mediafile(114, parent_id=113)
        self.set_models(
            {
                "group/3": {"meeting_mediafile_access_group_ids": [1]},
                "group/2": {
                    "meeting_mediafile_access_group_ids": [1],
                    "meeting_mediafile_inherited_access_group_ids": [1],
                },
                "meeting_mediafile/1": {
                    "mediafile_id": 112,
                    "meeting_id": 1,
                    "is_public": False,
                },
            }
        )
        response = self.request(
            "mediafile.update", {"id": 114, "meeting_id": 1, "access_group_ids": [2, 3]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/2",
            {
                "mediafile_id": 114,
                "meeting_id": 1,
                "access_group_ids": [2, 3],
                "inherited_access_group_ids": [2],
            },
        )
        self.assert_model_not_exists("meeting_mediafile/3")

    def test_update_access_group_on_published_root_mediafile(self) -> None:
        self.create_mediafile(111, is_directory=True)
        self.create_mediafile(112, is_directory=True, parent_id=111)
        self.create_mediafile(113, is_directory=True, parent_id=112)
        self.create_mediafile(114, parent_id=113)
        self.set_models(
            {
                "group/3": {"meeting_mediafile_access_group_ids": [1]},
                "group/2": {
                    "meeting_mediafile_access_group_ids": [1],
                    "meeting_mediafile_inherited_access_group_ids": [1],
                },
                "meeting_mediafile/1": {
                    "mediafile_id": 113,
                    "is_public": False,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.update", {"id": 111, "meeting_id": 1, "access_group_ids": [1, 3]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "mediafile_id": 113,
                "meeting_id": 1,
                "access_group_ids": [2, 3],
                "inherited_access_group_ids": [3],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/2",
            {
                "mediafile_id": 111,
                "meeting_id": 1,
                "access_group_ids": [1, 3],
                "inherited_access_group_ids": [1, 3],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/3",
            {
                "mediafile_id": 112,
                "meeting_id": 1,
                "access_group_ids": None,
                "inherited_access_group_ids": [1, 3],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/4",
            {
                "mediafile_id": 114,
                "meeting_id": 1,
                "access_group_ids": None,
                "inherited_access_group_ids": [3],
            },
        )

    def test_update_access_group_different_owner(self) -> None:
        self.create_meeting(4)
        self.permission_test_models["group/3"] = {"meeting_id": 4}
        self.set_models(self.permission_test_models)
        response = self.request(
            "mediafile.update",
            {"id": 111, "meeting_id": 1, "access_group_ids": [3]},
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

    def test_update_token_payload_old_token(self) -> None:
        self.set_models(
            {"mediafile/7": {"token": "token_1", "owner_id": ONE_ORGANIZATION_FQID}}
        )
        response = self.request("mediafile.update", {"id": 7, "token": "token_1"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/7", {"token": "token_1"})

    def test_update_title_parent_id_unique(self) -> None:
        self.create_mediafile(6, 1, is_directory=True)
        self.create_mediafile(7, 1, parent_id=6)
        self.create_mediafile(8, 1, parent_id=6)
        self.set_models(
            {
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
        response = self.request("mediafile.update", {"id": 8, "title": "file_7"})
        self.assert_status_code(response, 400)
        assert (
            "File 'file_7' already exists in folder 'folder_6'."
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
                "access_group_ids": [3],
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
                "access_group_ids": [3],
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
                "access_group_ids": [3],
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
        self.create_mediafile(111)
        self.base_permission_test(
            {},
            "mediafile.update",
            {"id": 111, "title": "title_Xcdfgee"},
            Permissions.Mediafile.CAN_MANAGE,
            fail=True,
        )

    def test_update_meeting_permissions_orga_owner_on_published_file(self) -> None:
        self.create_mediafile(111)
        self.base_permission_test(
            {},
            "mediafile.update",
            {"id": 111, "meeting_id": 1, "access_group_ids": [3]},
            Permissions.Mediafile.CAN_MANAGE,
        )
