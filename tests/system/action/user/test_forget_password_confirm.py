from urllib.parse import quote

from tests.system.action.base import BaseActionTestCase



class UserForgetPasswordConfirm(BaseActionTestCase):
    PW = "password"
    USERID = 1
    EMAIL = "test@ntvtn.de"

    def test_forget_password_confirm_correct(self) -> None:
        self.update_model("user/1", {"password": "old_pw", "email": self.EMAIL})
        token = quote(self.auth.create_authorization_token(self.USERID, self.EMAIL))
        response = self.request(
            "user.forget_password_confirm",
            {"user_id": 1, "authorization_token": token, "new_password": self.PW},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert self.auth.is_equals(self.PW, model.get("password", ""))

    def test_forget_password_confirm_user_id_mismatch(self) -> None:
        self.update_model("user/1", {"password": "old_pw", "email": self.EMAIL})
        token = quote(self.auth.create_authorization_token(self.USERID, self.EMAIL))
        response = self.request(
            "user.forget_password_confirm",
            {"user_id": 2, "authorization_token": token, "new_password": self.PW},
        )
        self.assert_status_code(response, 400)
        assert "Failed to verify token." == response.json["message"]
