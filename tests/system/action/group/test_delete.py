from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class GroupDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(22)
        self.set_models(
            {
                "meeting/22": {
                    "group_ids": [22, 23, 24, 111],
                },
                "group/111": {"name": "group", "meeting_id": 22},
            }
        )

    def test_delete_correct(self) -> None:
        response = self.request("group.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("group/111")

    def test_delete_wrong_id(self) -> None:
        response = self.request("group.delete", {"id": 112})
        self.assert_status_code(response, 400)
        model = self.get_model("group/111")
        assert model.get("name") == "group"

    def test_delete_default_group(self) -> None:
        self.set_models(
            {
                "meeting/22": {"default_group_id": 111},
                "group/111": {"default_group_for_meeting_id": 22},
            }
        )
        response = self.request("group.delete", {"id": 111})
        self.assert_status_code(response, 400)

    def test_delete_admin_group(self) -> None:
        self.set_models(
            {
                "meeting/22": {"admin_group_id": 111},
                "group/111": {"admin_group_for_meeting_id": 22},
            }
        )
        response = self.request("group.delete", {"id": 111})
        self.assert_status_code(response, 400)

    def test_delete_anonymous_group(self) -> None:
        self.set_models(
            {
                "meeting/22": {"anonymous_group_id": 111},
                "group/111": {"anonymous_group_for_meeting_id": 22},
            }
        )
        response = self.request("group.delete", {"id": 111})
        self.assert_status_code(response, 400)

    def test_delete_with_users(self) -> None:
        self.set_models(
            {
                "user/42": {
                    "meeting_user_ids": [142],
                    "meeting_ids": [22],
                    "committee_ids": [3],
                },
                "user/43": {
                    "meeting_user_ids": [143],
                    "meeting_ids": [22],
                    "committee_ids": [3],
                },
                "committee/3": {"meeting_ids": [22], "user_ids": [42, 43]},
                "meeting/22": {
                    "committee_id": 3,
                    "name": "name_meeting_22",
                    "group_ids": [111],
                    "user_ids": [42, 43],
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [142, 143],
                },
                "group/111": {
                    "name": "name_srtgb123",
                    "meeting_id": 22,
                    "meeting_user_ids": [142, 143],
                },
                "meeting_user/142": {
                    "meeting_id": 22,
                    "user_id": 42,
                    "group_ids": [111],
                },
                "meeting_user/143": {
                    "meeting_id": 22,
                    "user_id": 43,
                    "group_ids": [111],
                },
            }
        )
        response = self.request("group.delete", {"id": 111})

        self.assert_status_code(response, 400)
        self.assertEqual(
            response.json["message"], "You cannot delete a group with users."
        )

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "group/111": {"name": "name_srtgb123", "meeting_id": 1},
            },
            "group.delete",
            {"id": 111},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {
                "group/111": {"name": "name_srtgb123", "meeting_id": 1},
            },
            "group.delete",
            {"id": 111},
            Permissions.User.CAN_MANAGE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {
                "group/111": {"name": "name_srtgb123", "meeting_id": 1},
            },
            "group.delete",
            {"id": 111},
        )

    def test_delete_mediafile1(self) -> None:
        self.set_models(
            {
                "meeting/22": {
                    "group_ids": [111, 112],
                    "meeting_mediafile_ids": [1, 2],
                },
                "group/111": {
                    "meeting_mediafile_access_group_ids": [1, 2],
                    "meeting_mediafile_inherited_access_group_ids": [1, 2],
                },
                "group/112": {
                    "meeting_id": 22,
                    "meeting_mediafile_access_group_ids": [1],
                    "meeting_mediafile_inherited_access_group_ids": [1],
                },
                "meeting_mediafile/1": {
                    "access_group_ids": [111, 112],
                    "inherited_access_group_ids": [111, 112],
                    "is_public": False,
                    "meeting_id": 22,
                    "mediafile_id": 3,
                },
                "mediafile/3": {"meeting_mediafile_ids": [1]},
                "meeting_mediafile/2": {
                    "access_group_ids": [111],
                    "inherited_access_group_ids": [111],
                    "is_public": False,
                    "meeting_id": 22,
                    "mediafile_id": 1,
                },
                "mediafile/1": {"meeting_mediafile_ids": [2]},
            }
        )
        response = self.request("group.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted(
            "group/111",
            {
                "meeting_mediafile_access_group_ids": [1, 2],
                "meeting_mediafile_inherited_access_group_ids": [1, 2],
            },
        )
        self.assert_model_exists(
            "group/112",
            {
                "meeting_mediafile_access_group_ids": [1],
                "meeting_mediafile_inherited_access_group_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "is_public": False,
                "access_group_ids": [112],
                "inherited_access_group_ids": [112],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/2",
            {
                "is_public": True,
                "access_group_ids": [],
                "inherited_access_group_ids": [],
            },
        )

    def test_delete_mediafile2(self) -> None:
        self.set_models(
            {
                "meeting/22": {
                    "group_ids": [111, 112],
                    "meeting_mediafile_ids": [1, 2, 3, 4],
                },
                "group/111": {
                    "meeting_mediafile_access_group_ids": [1, 4],
                    "meeting_mediafile_inherited_access_group_ids": [1, 2, 3, 4],
                },
                "group/112": {
                    "meeting_id": 22,
                    "meeting_mediafile_access_group_ids": [4],
                    "meeting_mediafile_inherited_access_group_ids": [],
                },
                "mediafile/1": {
                    "child_ids": [2],
                    "is_directory": True,
                    "meeting_mediafile_ids": [1],
                },
                "meeting_mediafile/1": {
                    "mediafile_id": 1,
                    "access_group_ids": [111],
                    "inherited_access_group_ids": [111],
                    "is_public": False,
                    "meeting_id": 22,
                },
                "mediafile/2": {
                    "parent_id": 1,
                    "child_ids": [3, 4],
                    "is_directory": True,
                    "meeting_mediafile_ids": [2],
                },
                "meeting_mediafile/2": {
                    "mediafile_id": 2,
                    "inherited_access_group_ids": [111],
                    "is_public": False,
                    "meeting_id": 22,
                },
                "mediafile/3": {"parent_id": 2, "meeting_mediafile_ids": [3]},
                "meeting_mediafile/3": {
                    "mediafile_id": 3,
                    "inherited_access_group_ids": [111],
                    "is_public": False,
                    "meeting_id": 22,
                },
                "mediafile/4": {"parent_id": 2, "meeting_mediafile_ids": [3]},
                "meeting_mediafile/4": {
                    "mediafile_id": 4,
                    "access_group_ids": [111, 112],
                    "inherited_access_group_ids": [111],
                    "is_public": False,
                    "meeting_id": 22,
                },
            }
        )
        response = self.request("group.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted(
            "group/111",
            {
                "meeting_mediafile_access_group_ids": [1, 4],
                "meeting_mediafile_inherited_access_group_ids": [1, 2, 3, 4],
            },
        )
        self.assert_model_exists(
            "group/112",
            {
                "meeting_mediafile_access_group_ids": [4],
                "meeting_mediafile_inherited_access_group_ids": [4],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "is_public": True,
                "access_group_ids": [],
                "inherited_access_group_ids": [],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/2",
            {
                "is_public": True,
                "access_group_ids": None,
                "inherited_access_group_ids": [],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/3",
            {
                "is_public": True,
                "access_group_ids": None,
                "inherited_access_group_ids": [],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/4",
            {
                "is_public": False,
                "access_group_ids": [112],
                "inherited_access_group_ids": [112],
            },
        )

    def test_delete_mediafile3(self) -> None:
        self.set_models(
            {
                "meeting/22": {
                    "group_ids": [111, 112],
                    "meeting_mediafile_ids": [1, 2],
                },
                "group/111": {
                    "meeting_mediafile_access_group_ids": [1, 2],
                    "meeting_mediafile_inherited_access_group_ids": [1, 2],
                },
                "group/112": {
                    "meeting_id": 22,
                    "meeting_mediafile_access_group_ids": [2],
                    "meeting_mediafile_inherited_access_group_ids": [],
                },
                "mediafile/1": {
                    "child_ids": [2],
                    "is_directory": True,
                    "meeting_mediafile_ids": [1],
                },
                "meeting_mediafile/1": {
                    "mediafile_id": 1,
                    "access_group_ids": [111],
                    "inherited_access_group_ids": [111],
                    "is_public": False,
                    "meeting_id": 22,
                },
                "mediafile/2": {"parent_id": 1, "meeting_mediafile_ids": [2]},
                "meeting_mediafile/2": {
                    "mediafile_id": 2,
                    "access_group_ids": [111, 112],
                    "inherited_access_group_ids": [111],
                    "is_public": False,
                    "meeting_id": 22,
                },
            }
        )
        response = self.request_multi("group.delete", [{"id": 111}, {"id": 112}])

        self.assert_status_code(response, 200)
        self.assert_model_deleted(
            "group/111",
            {
                "meeting_mediafile_access_group_ids": [1, 2],
                "meeting_mediafile_inherited_access_group_ids": [1, 2],
            },
        )
        self.assert_model_deleted(
            "group/112",
            {
                "meeting_mediafile_access_group_ids": [2],
                "meeting_mediafile_inherited_access_group_ids": [2],
            },
        )
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
                "access_group_ids": [],
                "inherited_access_group_ids": [],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/2",
            {
                "is_public": True,
                "access_group_ids": [],
                "inherited_access_group_ids": [],
            },
        )
