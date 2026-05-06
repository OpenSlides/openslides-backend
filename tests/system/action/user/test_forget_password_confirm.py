from urllib.parse import quote

from tests.system.action.base import BaseActionTestCase


class UserForgetPasswordConfirm(BaseActionTestCase):
    EMAIL = "test@ntvtn.de"

    def setUp(self) -> None:
        super().setUp()
        self.reset_redis()
        self.set_models({"user/1": {"password": "old", "email": self.EMAIL}})

    def get_token(self, user_id: int = 1) -> str:
        return quote(self.auth.create_authorization_token(user_id, self.EMAIL))

    def test_forget_password_confirm_correct(self) -> None:
        response = self.request(
            "user.forget_password_confirm",
            {
                "user_id": 1,
                "authorization_token": self.get_token(),
                "new_password": "new",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        self.assertTrue(self.auth.is_equal("new", model["password"]))
        self.assert_logged_out()

    def test_forget_password_confirm_invalid_token(self) -> None:
        response = self.request(
            "user.forget_password_confirm",
            {"user_id": 1, "authorization_token": "invalid", "new_password": "new"},
            anonymous=True,
        )
        self.assert_status_code(response, 400)
        self.assertIn("Failed to verify token.", response.json["message"])

    def test_forget_password_confirm_user_id_mismatch(self) -> None:
        self.set_models(
            {
                "user/2": {"username": "u2"},
            }
        )
        response = self.request(
            "user.forget_password_confirm",
            {
                "user_id": 2,
                "authorization_token": self.get_token(),
                "new_password": "new",
            },
            anonymous=True,
        )
        self.assert_status_code(response, 400)
        self.assertIn("Failed to verify token.", response.json["message"])

    def test_forget_password_confirm_used_token(self) -> None:
        self.set_models(
            {"user/2": {"username": "dreamy", "password": "old", "email": self.EMAIL}}
        )
        token = self.get_token(2)
        response = self.request(
            "user.forget_password_confirm",
            {"user_id": 2, "authorization_token": token, "new_password": "new"},
            anonymous=True,
        )
        self.assert_status_code(response, 200)
        response = self.request(
            "user.forget_password_confirm",
            {"user_id": 2, "authorization_token": token, "new_password": "new2"},
            anonymous=True,
        )
        self.assert_status_code(response, 400)
        self.assertIn("Token is already used", response.json["message"])
        model = self.get_model("user/2")
        self.assertTrue(self.auth.is_equal("new", model["password"]))

    def test_forget_password_confirm_saml_id_error(self) -> None:
        self.set_models({"user/1": {"saml_id": "111"}})
        response = self.request(
            "user.forget_password_confirm",
            {
                "user_id": 1,
                "authorization_token": self.get_token(),
                "new_password": "new",
            },
            anonymous=True,
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "user 111 is a Single Sign On user and has no local OpenSlides password.",
            response.json["message"],
        )
