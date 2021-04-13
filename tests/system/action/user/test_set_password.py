from openslides_backend.permissions.permissions import OrganisationManagementLevel
from tests.system.action.base import BaseActionTestCase


class UserSetPasswordActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.update_model("user/1", {"password": "old_pw"})
        response = self.request("user.set_password", {"id": 1, "password": "test"})
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert self.auth.is_equals("test", model.get("password", ""))

    def test_update_correct_default_case(self) -> None:
        self.update_model("user/1", {"password": "old_pw"})
        response = self.request(
            "user.set_password", {"id": 1, "password": "test", "set_as_default": True}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert self.auth.is_equals("test", model.get("password", ""))
        assert "test" == model.get("default_password", "")

    def test_update_temporary(self) -> None:
        self.update_model("user/1", {"password": "old_pw", "meeting_id": 1})
        response = self.request(
            "user.set_password", {"id": 1, "password": "test", "set_as_default": True}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 1 in payload may not be a temporary user.", response.json["message"]
        )

    def test_generate_no_permissions(self) -> None:
        self.base_permission_test(
            {"user/10": {"username": "permission_test_user"}},
            "user.set_password",
            {"id": 10, "password": "test"},
        )

    def test_generate_permissions(self) -> None:
        self.base_permission_test(
            {"user/10": {"username": "permission_test_user"}},
            "user.set_password",
            {"id": 10, "password": "test"},
            OrganisationManagementLevel.CAN_MANAGE_USERS,
        )
