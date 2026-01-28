from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class MediafileCreateDirectoryActionTest(BaseActionTestCase):
    def test_create_directory_correct(self) -> None:
        self.create_meeting(110)
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
                "title": "title_Xcdfgee",
                "access_group_ids": [112],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/1",
            {
                "title": "title_Xcdfgee",
                "meeting_mediafile_ids": [1],
                "owner_id": "meeting/110",
                "is_directory": True,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "meeting_id": 110,
                "mediafile_id": 1,
                "access_group_ids": [112],
                "inherited_access_group_ids": [112],
                "is_public": False,
            },
        )

    def test_create_directory_organization_correct(self) -> None:
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": ONE_ORGANIZATION_FQID,
                "title": "title_Xcdfgee",
            },
        )
        self.assert_status_code(response, 200)
        mediafile = self.assert_model_exists(
            "mediafile/1",
            {
                "title": "title_Xcdfgee",
                "is_directory": True,
                "owner_id": ONE_ORGANIZATION_FQID,
            },
        )
        for field in ["inherited_access_group_ids", "is_public"]:
            assert field not in mediafile

    def test_create_directory_organization_with_published_parent(self) -> None:
        self.create_mediafile(1, is_directory=True)
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": ONE_ORGANIZATION_FQID,
                "title": "title_Xcdfgee",
                "parent_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        mediafile = self.assert_model_exists(
            "mediafile/2",
            {
                "parent_id": 1,
                "title": "title_Xcdfgee",
                "is_directory": True,
                "owner_id": ONE_ORGANIZATION_FQID,
                "published_to_meetings_in_organization_id": 1,
            },
        )
        for field in ["inherited_access_group_ids", "is_public"]:
            assert field not in mediafile
        self.assert_model_not_exists("meeting_mediafile/1")

    def test_create_directory_organization_with_published_parent_create_meeting_mediafiles(
        self,
    ) -> None:
        self.create_meeting()
        self.create_meeting(4)
        self.create_meeting(7)
        self.create_mediafile(1, is_directory=True)
        self.create_mediafile(2, is_directory=True)
        self.set_models(
            {
                "meeting_mediafile/11": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "is_public": True,
                },
                "meeting_mediafile/41": {
                    "meeting_id": 4,
                    "mediafile_id": 1,
                    "is_public": False,
                },
                "meeting_mediafile/42": {
                    "meeting_id": 4,
                    "mediafile_id": 2,
                    "is_public": False,
                },
                "group/5": {
                    "meeting_mediafile_access_group_ids": [41, 42],
                    "meeting_mediafile_inherited_access_group_ids": [41, 42],
                },
                "group/6": {
                    "meeting_mediafile_access_group_ids": [41, 42],
                    "meeting_mediafile_inherited_access_group_ids": [41, 42],
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": ONE_ORGANIZATION_FQID,
                "title": "title_Xcdfgee",
                "parent_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/3",
            {
                "parent_id": 1,
                "title": "title_Xcdfgee",
                "is_directory": True,
                "owner_id": ONE_ORGANIZATION_FQID,
                "published_to_meetings_in_organization_id": 1,
                "meeting_mediafile_ids": [43, 44],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/43",
            {
                "meeting_id": 1,
                "mediafile_id": 3,
                "is_public": True,
                "inherited_access_group_ids": None,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/44",
            {
                "meeting_id": 4,
                "mediafile_id": 3,
                "is_public": False,
                "inherited_access_group_ids": [5, 6],
            },
        )
        self.assert_model_not_exists("meeting_mediafile/45")

    def test_create_directory_parent(self) -> None:
        self.create_meeting(110)
        self.create_mediafile(110, 110, is_directory=True)
        self.set_models(
            {
                "meeting_mediafile/1100": {
                    "mediafile_id": 110,
                    "is_public": True,
                    "meeting_id": 110,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
                "title": "title_Xcdfgee",
                "access_group_ids": [112],
                "parent_id": 110,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/111",
            {
                "title": "title_Xcdfgee",
                "meeting_mediafile_ids": [1101],
                "parent_id": 110,
                "owner_id": "meeting/110",
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1101",
            {
                "meeting_id": 110,
                "mediafile_id": 111,
                "access_group_ids": [112],
                "inherited_access_group_ids": [112],
                "is_public": False,
            },
        )

    def test_create_directory_parent_inherited_list(self) -> None:
        self.create_meeting(110)
        self.create_mediafile(110, 110, is_directory=True)
        self.set_models(
            {
                "group/110": {
                    "meeting_mediafile_access_group_ids": [1100],
                    "meeting_mediafile_inherited_access_group_ids": [1100],
                },
                "meeting_mediafile/1100": {
                    "mediafile_id": 110,
                    "meeting_id": 110,
                    "is_public": False,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
                "title": "title_Xcdfgee",
                "access_group_ids": [112],
                "parent_id": 110,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/111",
            {
                "title": "title_Xcdfgee",
                "meeting_mediafile_ids": [1101],
                "parent_id": 110,
                "owner_id": "meeting/110",
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1101",
            {
                "meeting_id": 110,
                "mediafile_id": 111,
                "access_group_ids": [112],
                "inherited_access_group_ids": None,
                "is_public": False,
            },
        )

    def test_create_directory_parent_case1(self) -> None:
        self.create_meeting(110)
        self.create_mediafile(110, 110, is_directory=True)
        self.set_models(
            {
                "meeting_mediafile/1100": {
                    "mediafile_id": 110,
                    "meeting_id": 110,
                    "is_public": True,
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
        self.assert_model_exists(
            "mediafile/111",
            {
                "title": "title_Xcdfgee",
                "meeting_mediafile_ids": [1101],
                "parent_id": 110,
                "owner_id": "meeting/110",
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1101",
            {
                "meeting_id": 110,
                "mediafile_id": 111,
                "access_group_ids": None,
                "inherited_access_group_ids": None,
                "is_public": True,
            },
        )

    def test_create_directory_parent_case2(self) -> None:
        self.create_meeting(110)
        self.create_mediafile(110, 110, is_directory=True)
        self.set_models(
            {
                "group/112": {
                    "meeting_mediafile_access_group_ids": [1100],
                    "meeting_mediafile_inherited_access_group_ids": [1100],
                },
                "group/110": {
                    "meeting_mediafile_access_group_ids": [1100],
                    "meeting_mediafile_inherited_access_group_ids": [1100],
                },
                "meeting_mediafile/1100": {
                    "mediafile_id": 110,
                    "is_public": False,
                    "meeting_id": 110,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
                "title": "title_Xcdfgee",
                "access_group_ids": None,
                "parent_id": 110,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/111",
            {
                "title": "title_Xcdfgee",
                "meeting_mediafile_ids": [1101],
                "parent_id": 110,
                "owner_id": "meeting/110",
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1101",
            {
                "meeting_id": 110,
                "mediafile_id": 111,
                "access_group_ids": None,
                "inherited_access_group_ids": [110, 112],
                "is_public": False,
            },
        )

    def test_create_directory_parent_case3(self) -> None:
        self.create_meeting(110)
        self.create_mediafile(110, 110, is_directory=True)
        self.set_models(
            {
                "meeting_mediafile/1100": {
                    "mediafile_id": 110,
                    "is_public": True,
                    "meeting_id": 110,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
                "title": "title_Xcdfgee",
                "access_group_ids": [110, 112],
                "parent_id": 110,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/111",
            {
                "title": "title_Xcdfgee",
                "meeting_mediafile_ids": [1101],
                "parent_id": 110,
                "owner_id": "meeting/110",
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1101",
            {
                "meeting_id": 110,
                "mediafile_id": 111,
                "access_group_ids": [110, 112],
                "inherited_access_group_ids": [110, 112],
                "is_public": False,
            },
        )

    def test_create_directory_parent_case4(self) -> None:
        self.create_meeting(110)
        self.create_mediafile(110, 110, is_directory=True)
        self.set_models(
            {
                "group/110": {
                    "meeting_mediafile_access_group_ids": [1100],
                    "meeting_mediafile_inherited_access_group_ids": [1100],
                },
                "group/111": {
                    "meeting_mediafile_access_group_ids": [1100],
                    "meeting_mediafile_inherited_access_group_ids": [1100],
                },
                "meeting_mediafile/1100": {
                    "mediafile_id": 110,
                    "is_public": False,
                    "meeting_id": 110,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
                "title": "title_Xcdfgee",
                "access_group_ids": [110, 112],
                "parent_id": 110,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/111",
            {
                "title": "title_Xcdfgee",
                "meeting_mediafile_ids": [1101],
                "parent_id": 110,
                "owner_id": "meeting/110",
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1101",
            {
                "meeting_id": 110,
                "mediafile_id": 111,
                "access_group_ids": [110, 112],
                "inherited_access_group_ids": [110],
                "is_public": False,
            },
        )

    def test_create_directory_parent_case5(self) -> None:
        self.create_meeting(110)
        self.create_mediafile(110, 110, is_directory=True)
        self.set_models(
            {
                "group/110": {
                    "meeting_mediafile_access_group_ids": [1100],
                    "meeting_mediafile_inherited_access_group_ids": [1100],
                },
                "group/111": {
                    "meeting_mediafile_access_group_ids": [1100],
                    "meeting_mediafile_inherited_access_group_ids": [1100],
                },
                "meeting_mediafile/1100": {
                    "mediafile_id": 110,
                    "meeting_id": 110,
                    "is_public": False,
                },
            }
        )
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
                "title": "title_Xcdfgee",
                "access_group_ids": [112],
                "parent_id": 110,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/111",
            {
                "title": "title_Xcdfgee",
                "meeting_mediafile_ids": [1101],
                "parent_id": 110,
                "owner_id": "meeting/110",
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1101",
            {
                "meeting_id": 110,
                "mediafile_id": 111,
                "access_group_ids": [112],
                "inherited_access_group_ids": None,
                "is_public": False,
            },
        )

    def test_create_directory_no_access_group_ids(self) -> None:
        self.create_meeting(110)
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/110",
                "title": "title_UoOFrRU3INADQbay",
                "parent_id": None,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/1",
            {
                "owner_id": "meeting/110",
                "title": "title_UoOFrRU3INADQbay",
                "parent_id": None,
                "is_directory": True,
                "meeting_mediafile_ids": [1],
            },
        )

        # It is essential that a meeting_mediafile is always created for meeting mediafiles
        # since non-existence means that the access_group will be assumed to be the meetings
        # admin group. The below line therefore is essential to ensure the correct functionality.
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "meeting_id": 110,
                "mediafile_id": 1,
                "access_group_ids": None,
                "inherited_access_group_ids": None,
                "is_public": True,
            },
        )

    def test_create_directory_parent_id_parent_not_directory(self) -> None:
        self.create_meeting()
        self.create_mediafile(7, 1)
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
        self.create_meeting()
        self.create_meeting(4)
        self.create_mediafile(7, 1, is_directory=True)
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/4",
                "title": "title_1",
                "parent_id": 7,
            },
        )
        self.assert_status_code(response, 400)
        assert "Owner and parent don't match." in response.json["message"]

    def test_create_directory_mix_meeting_and_orga(self) -> None:
        self.create_meeting()
        self.create_mediafile(7, 1, is_directory=True)
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
        self.create_meeting()
        self.create_mediafile(6, 1, is_directory=True)
        self.create_mediafile(7, 1, parent_id=6)
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/1",
                "title": "file_7",
                "parent_id": 6,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "File 'file_7' already exists in folder 'folder_6'."
            in response.json["message"]
        )

    def test_create_directory_owner_access_groups_dont_match(self) -> None:
        self.create_meeting()
        self.create_meeting(4)
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/4",
                "title": "title_1",
                "access_group_ids": [3],
            },
        )
        self.assert_status_code(response, 400)
        assert "Owner and access groups don't match." in response.json["message"]

    def test_create_directory_access_groups_on_orga_owner(self) -> None:
        self.create_meeting()
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "organization/1",
                "title": "title_1",
                "access_group_ids": [3],
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "access_group_ids is not allowed in organization mediafiles."
            in response.json["message"]
        )

    def test_create_directory_two_meetings(self) -> None:
        self.create_meeting()
        self.create_meeting(4)
        response = self.request(
            "mediafile.create_directory",
            {
                "owner_id": "meeting/4",
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
            {},
            "mediafile.create_directory",
            {
                "owner_id": "meeting/1",
                "title": "title_Xcdfgee",
                "access_group_ids": [3],
            },
        )

    def test_create_directory_permissions(self) -> None:
        self.base_permission_test(
            {},
            "mediafile.create_directory",
            {
                "owner_id": "meeting/1",
                "title": "title_Xcdfgee",
                "access_group_ids": [3],
            },
            Permissions.Mediafile.CAN_MANAGE,
        )

    def test_create_directory_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "mediafile.create_directory",
            {
                "owner_id": "meeting/1",
                "title": "title_Xcdfgee",
                "access_group_ids": [3],
            },
        )

    def test_create_directory_no_permissions_orga_owner(self) -> None:
        self.base_permission_test(
            {},
            "mediafile.create_directory",
            {
                "owner_id": ONE_ORGANIZATION_FQID,
                "title": "title_Xcdfgee",
            },
        )

    def test_create_directory_permissions_orga_owner(self) -> None:
        self.base_permission_test(
            {},
            "mediafile.create_directory",
            {
                "owner_id": ONE_ORGANIZATION_FQID,
                "title": "title_Xcdfgee",
            },
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
