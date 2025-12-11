from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class GroupDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(22)

    def test_delete_correct(self) -> None:
        response = self.request("group.delete", {"id": 24})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("group/24")

    def test_delete_wrong_id(self) -> None:
        response = self.request("group.delete", {"id": 112})
        self.assert_status_code(response, 400)
        for nr in (22, 23, 24):
            self.assert_model_exists(f"group/{nr}", {"name": f"group{nr}"})

    def test_delete_default_group(self) -> None:
        self.set_models(
            {
                "meeting/22": {"default_group_id": 24},
                "group/24": {"default_group_for_meeting_id": 22},
            }
        )
        response = self.request("group.delete", {"id": 24})
        self.assert_status_code(response, 400)

    def test_delete_admin_group(self) -> None:
        self.set_models(
            {
                "meeting/22": {"admin_group_id": 24},
                "group/24": {"admin_group_for_meeting_id": 22},
            }
        )
        response = self.request("group.delete", {"id": 24})
        self.assert_status_code(response, 400)

    def test_delete_anonymous_group(self) -> None:
        self.set_models(
            {
                "meeting/22": {"anonymous_group_id": 24},
                "group/24": {"anonymous_group_for_meeting_id": 22},
            }
        )
        response = self.request("group.delete", {"id": 24})
        self.assert_status_code(response, 400)

    def test_delete_with_users(self) -> None:
        self.create_meeting(22)
        self.create_user("petunia", [24])
        self.create_user("vernon", [24])
        response = self.request("group.delete", {"id": 24})

        self.assert_status_code(response, 400)
        self.assertEqual(
            response.json["message"], "You cannot delete a group with users."
        )

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "group/24": {"name": "name_srtgb123", "meeting_id": 1},
            },
            "group.delete",
            {"id": 24},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {
                "group/24": {"name": "name_srtgb123", "meeting_id": 1},
            },
            "group.delete",
            {"id": 24},
            Permissions.User.CAN_MANAGE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {
                "group/24": {"name": "name_srtgb123", "meeting_id": 1},
            },
            "group.delete",
            {"id": 24},
        )

    def test_delete_mediafile1(self) -> None:
        self.create_mediafile(1, 22)
        self.create_mediafile(3, 22)
        self.set_models(
            {
                "group/24": {
                    "meeting_mediafile_access_group_ids": [1, 2],
                    "meeting_mediafile_inherited_access_group_ids": [1, 2],
                },
                "group/113": {
                    "name": "groupy",
                    "meeting_id": 22,
                    "meeting_mediafile_access_group_ids": [1],
                    "meeting_mediafile_inherited_access_group_ids": [1],
                },
                "meeting_mediafile/1": {
                    "is_public": False,
                    "meeting_id": 22,
                    "mediafile_id": 3,
                },
                "meeting_mediafile/2": {
                    "is_public": False,
                    "meeting_id": 22,
                    "mediafile_id": 1,
                },
            }
        )
        response = self.request("group.delete", {"id": 24})

        self.assert_status_code(response, 200)
        self.assert_model_not_exists("group/24")
        self.assert_model_exists(
            "group/113",
            {
                "meeting_mediafile_access_group_ids": [1],
                "meeting_mediafile_inherited_access_group_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "is_public": False,
                "access_group_ids": [113],
                "inherited_access_group_ids": [113],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/2",
            {
                "is_public": True,
                "access_group_ids": None,
                "inherited_access_group_ids": None,
            },
        )

    def test_delete_mediafile2(self) -> None:
        self.create_mediafile(1, 22, is_directory=True)
        self.create_mediafile(2, 22, is_directory=True, parent_id=1)
        self.create_mediafile(3, 22, parent_id=2)
        self.create_mediafile(4, 22, parent_id=2)
        self.set_models(
            {
                "group/24": {
                    "meeting_mediafile_access_group_ids": [1, 4],
                    "meeting_mediafile_inherited_access_group_ids": [1, 2, 3, 4],
                },
                "group/113": {
                    "name": "groupy",
                    "meeting_id": 22,
                    "meeting_mediafile_access_group_ids": [4],
                    "meeting_mediafile_inherited_access_group_ids": [],
                },
                "meeting_mediafile/1": {
                    "mediafile_id": 1,
                    "is_public": False,
                    "meeting_id": 22,
                },
                "meeting_mediafile/2": {
                    "mediafile_id": 2,
                    "is_public": False,
                    "meeting_id": 22,
                },
                "meeting_mediafile/3": {
                    "mediafile_id": 3,
                    "is_public": False,
                    "meeting_id": 22,
                },
                "meeting_mediafile/4": {
                    "mediafile_id": 4,
                    "is_public": False,
                    "meeting_id": 22,
                },
            }
        )
        response = self.request("group.delete", {"id": 24})

        self.assert_status_code(response, 200)
        self.assert_model_not_exists("group/24")
        self.assert_model_exists(
            "group/113",
            {
                "meeting_mediafile_access_group_ids": [4],
                "meeting_mediafile_inherited_access_group_ids": [4],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "is_public": True,
                "access_group_ids": None,
                "inherited_access_group_ids": None,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/2",
            {
                "is_public": True,
                "access_group_ids": None,
                "inherited_access_group_ids": None,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/3",
            {
                "is_public": True,
                "access_group_ids": None,
                "inherited_access_group_ids": None,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/4",
            {
                "is_public": False,
                "access_group_ids": [113],
                "inherited_access_group_ids": [113],
            },
        )

    def test_delete_mediafile3(self) -> None:
        self.create_mediafile(1, 22, is_directory=True)
        self.create_mediafile(2, 22, parent_id=1)
        self.set_models(
            {
                "group/24": {
                    "meeting_mediafile_access_group_ids": [1, 2],
                    "meeting_mediafile_inherited_access_group_ids": [1, 2],
                },
                "group/113": {
                    "name": "groupy",
                    "meeting_id": 22,
                    "meeting_mediafile_access_group_ids": [2],
                    "meeting_mediafile_inherited_access_group_ids": [],
                },
                "meeting_mediafile/1": {
                    "mediafile_id": 1,
                    "is_public": False,
                    "meeting_id": 22,
                },
                "meeting_mediafile/2": {
                    "mediafile_id": 2,
                    "is_public": False,
                    "meeting_id": 22,
                },
            }
        )
        response = self.request_multi("group.delete", [{"id": 24}, {"id": 113}])

        self.assert_status_code(response, 200)
        self.assert_model_not_exists("group/24")
        self.assert_model_not_exists("group/113")
        self.assert_model_exists(
            "mediafile/1",
            {
                "is_directory": True,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "is_public": True,
                "access_group_ids": None,
                "inherited_access_group_ids": None,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/2",
            {
                "is_public": True,
                "access_group_ids": None,
                "inherited_access_group_ids": None,
            },
        )
