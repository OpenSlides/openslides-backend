from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class GroupDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/22": {
                    "name": "name_meeting_22",
                    "group_ids": [111],
                    "is_active_in_organization_id": 1,
                },
                "group/111": {"name": "name_srtgb123", "meeting_id": 22},
            }
        )
        response = self.request("group.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("group/111")

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/22": {"name": "name_meeting_22", "group_ids": [111]},
                "group/112": {"name": "name_srtgb123", "meeting_id": 22},
            }
        )
        response = self.request("group.delete", {"id": 111})
        self.assert_status_code(response, 400)
        model = self.get_model("group/112")
        assert model.get("name") == "name_srtgb123"

    def test_delete_default_group(self) -> None:
        self.set_models(
            {
                "meeting/22": {"name": "name_meeting_22", "group_ids": [111]},
                "group/111": {
                    "name": "name_srtgb123",
                    "default_group_for_meeting_id": 22,
                    "meeting_id": 22,
                },
            }
        )
        response = self.request("group.delete", {"id": 111})

        self.assert_status_code(response, 400)

    def test_delete_admin_group(self) -> None:
        self.set_models(
            {
                "meeting/22": {"name": "name_meeting_22", "group_ids": [111]},
                "group/111": {
                    "name": "name_srtgb123",
                    "admin_group_for_meeting_id": 22,
                    "meeting_id": 22,
                },
            }
        )
        response = self.request("group.delete", {"id": 111})

        self.assert_status_code(response, 400)

    def test_delete_with_users(self) -> None:
        self.set_models(
            {
                "user/42": {"group_$22_ids": [111], "group_$_ids": ["22"]},
                "meeting/22": {
                    "name": "name_meeting_22",
                    "group_ids": [111],
                    "user_ids": [42],
                    "is_active_in_organization_id": 1,
                },
                "group/111": {
                    "name": "name_srtgb123",
                    "meeting_id": 22,
                    "user_ids": [42],
                },
            }
        )
        response = self.request("group.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("group/111")
        user = self.get_model("user/42")
        assert user.get("group_$22_ids") == []
        assert user.get("group_$_ids") == []
        user = self.get_model("meeting/22")
        assert user.get("user_ids") == []

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
