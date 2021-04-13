from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class UserUpdateSelfActionTest(BaseActionTestCase):
    def test_update_correct_permission(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("test", group_ids=[1])
        self.login(self.user_id)
        old_hash = self.auth.hash("old")
        self.update_model("user/2", {"password": old_hash})
        response = self.request(
            "user.set_password_self", {"old_password": "old", "new_password": "new"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/2")
        assert model.get("old_password") is None
        assert model.get("new_password") is None
        assert self.auth.is_equals("new", model.get("password", ""))

    def test_update_wrong_password(self) -> None:
        old_hash = self.auth.hash("old")
        self.update_model(
            "user/1",
            {"password": old_hash},
        )
        response = self.request(
            "user.set_password_self", {"old_password": "wrong", "new_password": "new"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("user/1")
        assert model.get("password") == old_hash

    def test_set_password_self_anonymus(self) -> None:
        response = self.request(
            "user.set_password_self",
            {"old_password": "wrong", "new_password": "new"},
            anonymous=True,
        )
        self.assert_status_code(response, 400)
        self.assertIn("Can't set password for anonymous", response.json["message"])

    def test_set_password_self_temporary_permissions(self) -> None:
        self.create_meeting()
        self.set_group_permissions(1, [Permissions.User.CAN_CHANGE_OWN_PASSWORD])
        self.user_id = self.create_user("test", group_ids=[1])
        self.login(self.user_id)
        old_hash = self.auth.hash("old")
        self.update_model("user/2", {"password": old_hash, "meeting_id": 1})
        response = self.request(
            "user.set_password_self", {"old_password": "old", "new_password": "new"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/2")
        assert self.auth.is_equals("new", model.get("password", ""))

    def test_set_password_self_temporary_no_permissions(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("test", group_ids=[1])
        self.login(self.user_id)
        old_hash = self.auth.hash("old")
        self.update_model("user/2", {"password": old_hash, "meeting_id": 1})
        response = self.request(
            "user.set_password_self", {"old_password": "old", "new_password": "new"}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.set_password_self. Missing permission: user.can_change_own_password",
            response.json["message"],
        )
