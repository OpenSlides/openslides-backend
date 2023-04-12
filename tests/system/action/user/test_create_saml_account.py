from tests.system.action.base import BaseActionTestCase


class UserCreateSamlAccount(BaseActionTestCase):
    def test_create_saml_account_correct(self) -> None:
        response = self.request(
            "user.create_saml_account",
            {"saml_id": "111222333", "first_name": "Max", "last_name": "Mustermann"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "111222333",
                "saml_id": "111222333",
                "first_name": "Max",
                "last_name": "Mustermann",
            },
        )

    def test_create_saml_account_full_fields(self) -> None:
        response = self.request(
            "user.create_saml_account",
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
            "user/2",
            {
                "username": "111222333",
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

    def test_create_saml_account_saml_id_exists(self) -> None:
        self.set_models({"user/78": {"username": "111222333", "saml_id": "111222333"}})
        response = self.request(
            "user.create_saml_account",
            {"saml_id": "111222333", "first_name": "Max", "last_name": "Mustermann"},
        )
        self.assert_status_code(response, 400)
        assert "Saml_id already exists." in response.json["message"]

    def test_create_saml_account_user_exists(self) -> None:
        self.set_models(
            {
                "user/78": {
                    "username": "test",
                    "saml_id": "222333444",
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "email": "max@mustermann.com",
                }
            }
        )
        response = self.request(
            "user.create_saml_account",
            {
                "saml_id": "111222333",
                "first_name": "Max",
                "last_name": "Mustermann",
                "email": "max@mustermann.com",
            },
        )
        self.assert_status_code(response, 400)
        assert "User with name and email already exists." in response.json["message"]
