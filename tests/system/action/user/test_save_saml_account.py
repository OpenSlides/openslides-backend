from datastore.shared.di import injector
from datastore.shared.postgresql_backend import ConnectionHandler

from tests.system.action.base import BaseActionTestCase


class UserBaseSamlAccount(BaseActionTestCase):
    def setUp(self) -> None:
        self.results = {
            "saml_id": "111222333",
            "title": "Dr.",
            "first_name": "Max",
            "last_name": "Mustermann",
            "email": "test@example.com",
            "gender": "male",
            "pronoun": "er",
            "is_active": True,
            "is_physical_person": True,
        }

        super().setUp()
        self.set_models(
            {
                "organization/1": {
                    "saml_enabled": True,
                    "saml_attr_mapping": {
                        "saml_id": "username",
                        "title": "title",
                        "first_name": "firstName",
                        "last_name": "lastName",
                        "email": "email",
                        "gender": "gender",
                        "pronoun": "pronoun",
                        "is_active": "is_active",
                        "is_physical_person": "is_person",
                    },
                }
            }
        )


class UserCommonSamlAccount(UserBaseSamlAccount):
    def test_sso_disabled_error(self) -> None:
        self.update_model("organization/1", {"saml_enabled": False})
        response = self.request("user.save_saml_account", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "SingleSignOn is not enabled in OpenSlides configuration",
            response.json["message"],
        )

    def test_saml_attr_mapping_empty(self) -> None:
        self.update_model("organization/1", {"saml_attr_mapping": {}})
        response = self.request("user.save_saml_account", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "SingleSignOn field attributes are not configured in OpenSlides",
            response.json["message"],
        )

    def test_save_attr_no_saml_id_provided(self) -> None:
        """error message: example data username from IdP maps to saml_id as OpenSlides name"""
        response = self.request(
            "user.save_saml_account", {"firstName": "Joe", "lastName": "Cartwright"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['username'] properties",
            response.json["message"],
        )

    def test_save_more_than_one_user_instances_provided(self) -> None:
        response = self.request_multi(
            "user.save_saml_account", [{"username": "Joe"}, {"username": "Ben"}]
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain less than or equal to 1 items",
            response.json["message"],
        )

    def test_suppress_not_allowed_field(self) -> None:
        self.set_models(
            {
                "organization/1": {
                    "saml_enabled": True,
                    "saml_attr_mapping": {
                        "saml_id": "username",
                        "default_structure_level": "default_structure_level",
                    },
                }
            }
        )
        response = self.request(
            "user.save_saml_account",
            {"username": "Joe", "default_structure_level": "Cartwright"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2", {"username": "Joe", "default_structure_level": None}
        )


class UserCreateSamlAccount(UserBaseSamlAccount):
    def test_create_saml_account_all_fields(self) -> None:
        response = self.request(
            "user.save_saml_account",
            {
                "username": "111222333",
                "title": "Dr.",
                "firstName": "Max",
                "lastName": "Mustermann",
                "email": "test@example.com",
                "gender": "male",
                "pronoun": "er",
                "is_active": True,
                "is_person": True,
            },
        )
        self.assert_status_code(response, 200)
        assert (
            response.json["results"][0][0]["user_id"] == 2
        ), "Missing user_id in result"
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

    def test_create_saml_account_all_fields_as_list(self) -> None:
        response = self.request(
            "user.save_saml_account",
            {
                "username": ["111222333"],
                "title": ["Dr."],
                "firstName": ["Max"],
                "lastName": ["Mustermann"],
                "email": ["test@example.com"],
                "gender": ["male"],
                "pronoun": ["er"],
                "is_active": [True],
                "is_person": [True],
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

    def test_create_saml_account_username_exists(self) -> None:
        self.set_models(
            {
                "user/78": {
                    "username": "SAMLID",
                }
            }
        )
        response = self.request(
            "user.save_saml_account",
            {
                "username": "SAMLID",
                "firstName": "Max",
                "lastName": "Mustermann",
                "email": "max@mustermann.com",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/79",
            {
                "saml_id": "SAMLID",
                "username": "SAMLID1",
                "first_name": "Max",
                "last_name": "Mustermann",
                "email": "max@mustermann.com",
            },
        )
        self.assert_model_exists(
            "user/78",
            {
                "saml_id": None,
                "username": "SAMLID",
            },
        )


class UserUpdateSamlAccount(UserBaseSamlAccount):
    connection_handler = injector.get(ConnectionHandler)

    @classmethod
    def get_current_db_position(cls) -> int:
        with cls.connection_handler.get_connection_context():
            with cls.connection_handler.get_current_connection().cursor() as cursor:
                cursor.execute("select max(position) from positions;")
                return cursor.fetchone()[0]

    def test_update_saml_account_correct(self) -> None:
        self.set_models({"user/78": {"username": "111222333", "saml_id": "111222333"}})
        response = self.request(
            "user.save_saml_account",
            {
                "username": "111222333",
                "title": "Dr.",
                "firstName": "Max",
                "lastName": "Mustermann",
            },
        )
        self.assert_status_code(response, 200)
        assert (
            response.json["results"][0][0]["user_id"] == 78
        ), "Missing user_id in result"
        self.assert_model_exists(
            "user/78",
            {
                "saml_id": "111222333",
                "username": "111222333",
                "title": "Dr.",
                "first_name": "Max",
                "last_name": "Mustermann",
            },
        )

    def test_update_saml_account_all_fields(self) -> None:
        self.set_models({"user/78": {"username": "Saml", "saml_id": "111222333"}})
        response = self.request(
            "user.save_saml_account",
            {
                "username": "111222333",
                "title": "Dr.",
                "firstName": "Max",
                "lastName": "Mustermann",
                "email": "test@example.com",
                "gender": "male",
                "pronoun": "er",
                "is_active": True,
                "is_person": True,
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

    def test_update_saml_account_change_nothing(self) -> None:
        user_data = {
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
        }

        self.set_models({"user/78": user_data})
        old_position = self.get_current_db_position()
        response = self.request(
            "user.save_saml_account",
            {
                "username": "111222333",
                "title": "Dr.",
                "firstName": "Max",
                "lastName": "Mustermann",
                "email": "test@example.com",
                "gender": "male",
                "pronomen": "er",
                "is_active": True,
                "is_person": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/78", user_data)
        new_position = self.get_current_db_position()
        assert new_position == old_position
