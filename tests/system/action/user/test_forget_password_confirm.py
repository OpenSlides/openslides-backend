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
        assert self.auth.is_equal(self.PW, model.get("password", ""))
        self.assert_logged_out()

    def test_forget_password_confirm_invalid_token(self) -> None:
        self.update_model("user/1", {"password": "old_pw", "email": self.EMAIL})
        token = "aaa.bbb.ccc"
        response = self.request(
            "user.forget_password_confirm",
            {"user_id": 1, "authorization_token": token, "new_password": self.PW},
        )
        self.assert_status_code(response, 400)
        assert "Failed to verify token." in response.json["message"]

    def test_forget_password_confirm_user_id_mismatch(self) -> None:
        self.set_models(
            {
                "user/1": {"password": "old_pw", "email": self.EMAIL},
                "user/2": {"username": "u2"},
            }
        )
        token = quote(self.auth.create_authorization_token(self.USERID, self.EMAIL))
        response = self.request(
            "user.forget_password_confirm",
            {"user_id": 2, "authorization_token": token, "new_password": self.PW},
        )
        self.assert_status_code(response, 400)
        assert "Failed to verify token." == response.json["message"]

    def test_forget_password_confirm_saml_id_error(self) -> None:
        self.update_model(
            "user/1", {"password": "pw", "email": self.EMAIL, "saml_id": "111"}
        )
        token = quote(self.auth.create_authorization_token(self.USERID, self.EMAIL))
        response = self.request(
            "user.forget_password_confirm",
            {"user_id": 1, "authorization_token": token, "new_password": self.PW},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "user 111 is a Single Sign On user and has no local OpenSlides password.",
            response.json["message"],
        )
