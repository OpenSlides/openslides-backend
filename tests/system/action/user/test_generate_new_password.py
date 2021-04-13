from openslides_backend.permissions.permissions import OrganisationManagementLevel
from tests.system.action.base import BaseActionTestCase


class UserGenerateNewPaswordActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.update_model("user/1", {"password": "old_pw"})
        response = self.request("user.generate_new_password", {"id": 1})
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert model.get("password") is not None
        assert self.auth.is_equals(
            model.get("default_password", ""), model.get("password", "")
        )

    def test_update_temporary(self) -> None:
        self.update_model("user/1", {"password": "old_pw", "meeting_id": 1})
        response = self.request("user.generate_new_password", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 1 in payload may not be a temporary user.", response.json["message"]
        )

    def test_generate_no_permissions(self) -> None:
        self.base_permission_test(
            {"user/10": {"username": "permission_test_user"}},
            "user.generate_new_password",
            {"id": 10},
        )

    def test_generate_permissions(self) -> None:
        self.base_permission_test(
            {"user/10": {"username": "permission_test_user"}},
            "user.generate_new_password",
            {"id": 10},
            OrganisationManagementLevel.CAN_MANAGE_USERS,
        )
