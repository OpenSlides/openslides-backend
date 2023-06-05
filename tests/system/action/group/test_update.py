from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class GroupUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/111": {
                    "name": "name_srtgb123",
                    "meeting_id": 1,
                    "permissions": [Permissions.User.CAN_MANAGE],
                },
            }
        )

    def test_update_correct(self) -> None:
        response = self.request("group.update", {"id": 111, "name": "name_Xcdfgee"})
        self.assert_status_code(response, 200)
        model = self.get_model("group/111")
        assert model.get("name") == "name_Xcdfgee"

    def test_update_permissions(self) -> None:
        data = [
            Permissions.User.CAN_MANAGE,
            Permissions.Motion.CAN_MANAGE,
            Permissions.ListOfSpeakers.CAN_BE_SPEAKER,
        ]
        response = self.request(
            "group.update",
            {
                "id": 111,
                "permissions": data,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/111")
        assert model.get("permissions") == data

    def test_update_permissions_remove(self) -> None:
        response = self.request(
            "group.update", {"id": 111, "permissions": [Permissions.Motion.CAN_MANAGE]}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/111")
        assert model.get("permissions") == [Permissions.Motion.CAN_MANAGE]

    def test_update_permissions_redundant(self) -> None:
        response = self.request(
            "group.update",
            {
                "id": 111,
                "permissions": [Permissions.User.CAN_MANAGE, Permissions.User.CAN_SEE],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/111")
        assert model.get("permissions") == [Permissions.User.CAN_MANAGE]

    def test_update_wrong_id(self) -> None:
        response = self.request("group.update", {"id": 112, "name": "name_Xcdfgee"})
        self.assert_status_code(response, 400)
        model = self.get_model("group/111")
        assert model.get("name") == "name_srtgb123"

    def test_update_forbidden(self) -> None:
        self.base_permission_test(
            {},
            "group.update",
            {"id": 111, "name": "name_Xcdfgee"},
        )

    def test_update_allowed(self) -> None:
        self.base_permission_test(
            {},
            "group.update",
            {"id": 111, "name": "name_Xcdfgee"},
            Permissions.User.CAN_MANAGE,
        )
