from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class GroupUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def test_update_correct(self) -> None:
        response = self.request("group.update", {"id": 3, "name": "name_Xcdfgee"})
        self.assert_status_code(response, 200)
        model = self.get_model("group/3")
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
                "id": 3,
                "permissions": data,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/3")
        assert model.get("permissions") == data

    def test_update_permissions_remove(self) -> None:
        response = self.request(
            "group.update", {"id": 3, "permissions": [Permissions.Motion.CAN_MANAGE]}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/3")
        assert model.get("permissions") == [Permissions.Motion.CAN_MANAGE]

    def test_update_permissions_redundant(self) -> None:
        response = self.request(
            "group.update",
            {
                "id": 3,
                "permissions": [Permissions.User.CAN_MANAGE, Permissions.User.CAN_SEE],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/3")
        assert model.get("permissions") == [Permissions.User.CAN_MANAGE]

    def test_update_wrong_id(self) -> None:
        response = self.request("group.update", {"id": 112, "name": "name_Xcdfgee"})
        self.assert_status_code(response, 400)

    def test_update_external_id_forbidden(self) -> None:
        self.set_organization_management_level(None)
        self.set_user_groups(1, [3])
        self.add_group_permissions(3, [Permissions.User.CAN_MANAGE])
        response = self.request("group.update", {"id": 3, "external_id": "test"})
        self.assert_status_code(response, 403)

    def test_update_external_id_allowed(self) -> None:
        self.set_organization_management_level(None)
        self.set_user_groups(1, [2])
        response = self.request("group.update", {"id": 3, "external_id": "test"})
        self.assert_status_code(response, 200)

    def test_update_external_id_not_unique(self) -> None:
        external_id = "external_id"
        self.update_model("group/2", {"external_id": external_id})
        response = self.request("group.update", {"id": 3, "external_id": external_id})
        self.assert_status_code(response, 400)
        self.assertIn(
            "The external_id of the group is not unique in the meeting scope.",
            response.json["message"],
        )

    def test_update_external_id_self(self) -> None:
        external_id = "external_id"
        self.update_model("group/2", {"external_id": external_id, "name": "group2"})
        response = self.request(
            "group.update", {"id": 2, "external_id": external_id, "name": "grp2"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/2", {"external_id": external_id, "name": "grp2"}
        )

    def test_update_forbidden(self) -> None:
        self.base_permission_test(
            {},
            "group.update",
            {"id": 3, "name": "name_Xcdfgee"},
        )

    def test_update_allowed(self) -> None:
        self.base_permission_test(
            {},
            "group.update",
            {"id": 3, "name": "name_Xcdfgee"},
            Permissions.User.CAN_MANAGE,
        )

    def test_update_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "group.update",
            {"id": 3, "name": "name_Xcdfgee"},
        )
