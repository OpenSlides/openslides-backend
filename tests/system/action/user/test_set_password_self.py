from tests.system.action.base import BaseActionTestCase


class UserSetPasswordSelfActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.reset_redis()

    def test_set_password_correct_permission(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("test", group_ids=[1])
        self.login(self.user_id)
        old_hash = self.auth.hash("old")
        self.update_model(
            "user/2", {"password": old_hash, "can_change_own_password": True}
        )
        response = self.request(
            "user.set_password_self", {"old_password": "old", "new_password": "new"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/2")
        assert model.get("old_password") is None
        assert model.get("new_password") is None
        assert self.auth.is_equal("new", model.get("password", ""))
        self.assert_logged_out()

    def test_set_password_wrong_password(self) -> None:
        old_hash = self.auth.hash("old")
        self.update_model(
            "user/1",
            {"password": old_hash, "can_change_own_password": True},
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
        self.assert_status_code(response, 403)
        self.assertIn(
            "Anonymous is not allowed to execute user.set_password_self",
            response.json["message"],
        )

    def test_set_password_self_no_permissions(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("test", group_ids=[1])
        self.login(self.user_id)
        old_hash = self.auth.hash("old")
        self.update_model(
            "user/2",
            {
                "password": old_hash,
                "can_change_own_password": False,
            },
        )
        response = self.request(
            "user.set_password_self", {"old_password": "old", "new_password": "new"}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You cannot change your password.",
            response.json["message"],
        )

    def test_set_password_idp_id_error(self) -> None:
        self.update_model("user/1", {"idp_id": "111", "can_change_own_password": True})
        response = self.request(
            "user.set_password_self", {"old_password": "old", "new_password": "new"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "user 111 is a Single Sign On user and has no local OpenSlides password.",
            response.json["message"],
        )
