from tests.system.action.base import BaseActionTestCase


class UserUpdateSamlAccount(BaseActionTestCase):
    def test_update_saml_account_correct(self) -> None:
        self.set_models({"user/78": {"username": "111222333", "saml_id": "111222333"}})
        response = self.request(
            "user.update_saml_account",
            {
                "saml_id": "111222333",
                "title": "Dr.",
                "first_name": "Max",
                "last_name": "Mustermann",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/78",
            {
                "saml_id": "111222333",
                "title": "Dr.",
                "first_name": "Max",
                "last_name": "Mustermann",
            },
        )

    def test_update_saml_account_all_fields(self) -> None:
        self.set_models({"user/78": {"username": "Saml", "saml_id": "111222333"}})
        response = self.request(
            "user.update_saml_account",
            {
                "saml_id": "111222333",
                "title": "Dr.",
                "first_name": "Max",
                "last_name": "Mustermann",
                "email": "test@example.com",
                "gender": "male",
                "pronoun": "er",
                "is_active": True,
                "is_physical_person": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/78",
            {
                "saml_id": "111222333",
                "username": "Saml",
                "title": "Dr.",
                "first_name": "Max",
                "last_name": "Mustermann",
                "email": "test@example.com",
                "gender": "male",
                "pronoun": "er",
                "is_active": True,
                "is_physical_person": True,
            },
        )

    def test_update_saml_account_missing_user(self) -> None:
        response = self.request(
            "user.update_saml_account",
            {
                "saml_id": "111222333",
                "title": "Dr.",
                "first_name": "Max",
                "last_name": "Mustermann",
            },
        )
        self.assert_status_code(response, 400)
        assert "Wrong saml_id." in response.json["message"]
