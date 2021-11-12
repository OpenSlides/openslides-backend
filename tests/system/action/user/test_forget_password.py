from time import time

from openslides_backend.action.mixins.send_email_mixin import EmailSettings
from tests.system.action.base import BaseActionTestCase
from tests.system.action.mail_base import (
    AIOHandler,
    AiosmtpdServerManager,
    set_test_email_settings,
)


class UserForgetPassword(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        set_test_email_settings()

    def test_forget_password_send_mail_correct(self) -> None:
        self.set_models({"user/1": {"email": "test@ntvtn.de"}})
        start_time = int(time())
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request("user.forget_password", {"email": "test@ntvtn.de"})
        self.assert_status_code(response, 200)
        user = self.get_model("user/1")
        assert user.get("last_email_send", 0) >= start_time
        assert handler.emails[0]["from"] == EmailSettings.default_from_email
        assert "Reset your OpenSlides password" in handler.emails[0]["data"]

    def test_forget_password_two_users_with_email(self) -> None:
        self.set_models(
            {
                "user/1": {"email": "test@ntvtn.de"},
                "user/2": {"email": "test@ntvtn.de", "username": "test2"},
                "user/3": {"email": "user@ntvtn.de", "username": "test3"},
            }
        )
        start_time = int(time())
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request("user.forget_password", {"email": "test@ntvtn.de"})
        self.assert_status_code(response, 200)
        user = self.get_model("user/1")
        assert user.get("last_email_send", 0) >= start_time
        user2 = self.get_model("user/2")
        assert user2.get("last_email_send", 0) >= start_time
        user3 = self.get_model("user/3")
        assert user3.get("last_email_send", 0) == 0
        assert handler.emails[0]["from"] == EmailSettings.default_from_email
        assert handler.emails[0]["to"][0] == "test@ntvtn.de"
        assert "For completeness your username: admin" in handler.emails[0]["data"]
        assert handler.emails[1]["from"] == EmailSettings.default_from_email
        assert handler.emails[1]["to"][0] == "test@ntvtn.de"
        assert "For completeness your username: test2" in handler.emails[1]["data"]

    def test_forget_password_no_user_found(self) -> None:
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request("user.forget_password", {"email": "info@ntvtn.de"})
        self.assert_status_code(response, 200)
        assert not handler.emails

    def test_forget_password_invalid_default_from_email(self) -> None:
        EmailSettings.default_from_email = "grüllegrütz"
        response = self.request("user.forget_password", {"email": "test@ntvtn.de"})
        self.assert_status_code(response, 400)
        assert (
            "The server was configured improperly. Please contact your administrator."
            == response.json["message"]
        )

    def test_forget_password_send_invalid_email_adress(self) -> None:
        response = self.request("user.forget_password", {"email": "grüllegrütz"})
        self.assert_status_code(response, 400)
        assert "'grüllegrütz' is not a valid email adress." == response.json["message"]

    def test_forget_password_wrong_email_password(self) -> None:
        EmailSettings.password = "not secret"
        EmailSettings.user = "sender@example.com"

        self.set_models({"user/1": {"email": "test@ntvtn.de"}})
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request("user.forget_password", {"email": "test@ntvtn.de"})
        self.assert_status_code(response, 400)
        assert (
            "The server was configured improperly. Please contact your administrator."
            in response.json["message"]
        )
