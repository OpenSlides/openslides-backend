from datastore.shared.di import injector
from datastore.shared.postgresql_backend import ConnectionHandler

from tests.system.action.base import BaseActionTestCase


class UserBaseSamlAccount(BaseActionTestCase):
    def setUp(self) -> None:
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
                    "gender_ids": [1, 2, 3, 4],
                },
                "gender/1": {"organization_id": 1, "name": "male"},
                "gender/2": {"organization_id": 1, "name": "female"},
                "gender/3": {"organization_id": 1, "name": "diverse"},
                "gender/4": {"organization_id": 1, "name": "non-binary"},
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
        response = self.request(
            "user.save_saml_account", {"firstName": "Joe", "lastName": "Cartwright"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['username'] properties",
            response.json["message"],
        )

    def test_save_attr_empty_saml_id_provided(self) -> None:
        response = self.request(
            "user.save_saml_account", {"username": "", "lastName": "Cartwright"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.username must be valid exactly by one definition (0 matches found)",
            response.json["message"],
        )

    def test_save_attr_empty_saml_id_list_provided(self) -> None:
        response = self.request(
            "user.save_saml_account", {"username": [], "lastName": "Cartwright"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.username must be valid exactly by one definition (0 matches found)",
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
                        "default_number": "default_number",
                    },
                }
            }
        )
        response = self.request(
            "user.save_saml_account",
            {"username": "Joe", "default_number": "Cartwright"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "Joe", "default_number": None})

    def test_create_new_gender(self) -> None:
        response = self.request(
            "user.save_saml_account",
            {
                "username": "111222333",
                "gender": "cloud",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "111222333",
                "gender_id": 5,
            },
        )
        self.assert_model_exists("gender/5", {"name": "cloud"})


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
                "gender_id": 1,
                "pronoun": "er",
                "is_active": True,
                "is_physical_person": True,
                "can_change_own_password": False,
                "default_password": None,
                "password": None,
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
                "gender_id": 1,
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
        self.set_models(
            {
                "user/78": {"username": "Saml", "saml_id": "111222333", "gender_id": 4},
            }
        )
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
                "gender_id": 1,
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
            "gender_id": 1,
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

    def test_create_saml_account_all_fields_mixed_changes(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "saml_id": "111222333",
                    "username": "Saml",
                    "title": "Dr.",
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "email": "test@example.com",
                    "gender_id": 1,
                    "pronoun": "er",
                    "is_active": True,
                    "is_physical_person": True,
                }
            }
        )
        response = self.request(
            "user.save_saml_account",
            {
                "username": ["111222333"],
                "title": "Drx.",
                "firstName": ["Maxx"],
                "lastName": [],  # don't change
                "email": [""],
                "pronoun": [None],  # don't change
                "is_active": False,
                "is_person": None,  # don't change
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "Saml",
                "saml_id": "111222333",
                "title": "Drx.",
                "first_name": "Maxx",
                "last_name": "Mustermann",
                "email": "",
                "gender_id": 1,
                "pronoun": "er",
                "is_active": False,
                "is_physical_person": True,
            },
        )

    def test_gender_to_none(self) -> None:
        self.set_models(
            {
                "user/78": {"username": "Saml", "saml_id": "111222333", "gender_id": 4},
            }
        )
        response = self.request(
            "user.save_saml_account",
            {
                "username": "111222333",
                "title": "Dr.",
                "firstName": "Max",
                "lastName": "Mustermann",
                "gender": "",
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
                "gender_id": None,
            },
        )


class UserSamlAccountBoolean(UserBaseSamlAccount):
    def test_create_saml_account_boolean_defaults(self) -> None:
        response = self.request(
            "user.save_saml_account",
            {
                "username": ["111222333"],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "111222333",
                "saml_id": "111222333",
                "title": None,
                "first_name": None,
                "last_name": None,
                "email": None,
                "gender_id": None,
                "pronoun": None,
                "is_active": True,
                "is_physical_person": True,
            },
        )

    def test_create_saml_account_boolean_string_types_true_N(self) -> None:
        response = self.request(
            "user.save_saml_account",
            {"username": ["111"], "is_active": "true", "is_person": "N"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "111",
                "saml_id": "111",
                "is_active": True,
                "is_physical_person": False,
            },
        )

    def test_create_saml_account_boolean_string_types_error(self) -> None:
        response = self.request(
            "user.save_saml_account", {"username": ["111"], "is_active": "tru"}
        )
        self.assert_status_code(response, 400)
        self.assertIn("Could not parse tru, expect boolean", response.json["message"])

    def test_create_saml_account_boolean_integer_types_1_0(self) -> None:
        response = self.request(
            "user.save_saml_account",
            {"username": ["111"], "is_active": 1, "is_person": 0},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "111",
                "saml_id": "111",
                "is_active": True,
                "is_physical_person": False,
            },
        )

    def test_create_saml_account_boolean_integer_types_error(self) -> None:
        response = self.request(
            "user.save_saml_account", {"username": ["111"], "is_active": 2}
        )
        self.assert_status_code(response, 400)
        self.assertIn("Could not parse 2, expect boolean", response.json["message"])


class UserAddToGroup(UserBaseSamlAccount):
    def setUp(self) -> None:
        super().setUp()
        self.organization = {
            "saml_enabled": True,
            "saml_attr_mapping": {
                "member_number": "member_number",
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
        self.meeting_mappers = [
            {
                "name": "works",
                "external_id": "Landtag",
                "conditions": [
                    {"attribute": "member_number", "condition": "LV_.*"},
                    {
                        "attribute": "email",
                        "condition": "[\\w\\.]+@([\\w-]+\\.)+[\\w]{2,4}",
                    },
                ],
                "mappings": {
                    "comment": {
                        "attribute": "idp_commentary",
                        "default": "Vote weight, groups and structure levels set via SSO.",
                    },
                    "number": {"attribute": "participant_number"},
                    "structure_levels": [
                        {
                            "attribute": "structure",
                            "default": "structure1",
                        }
                    ],
                    "groups": [
                        {
                            "attribute": "idp_group_attribute",
                            "default": "not_a_group",
                        }
                    ],
                    "vote_weight": {"attribute": "vw", "default": "1.000000"},
                    "present": {"attribute": "presence", "default": "True"},
                },
            },
            {
                "name": "works_too",
                "external_id": "Kreistag",
                "conditions": [{"attribute": "kv_member_number", "condition": "KV_.*"}],
                "mappings": {
                    "comment": {
                        "attribute": "idp_commentary",
                        "default": "Vote weight, groups and structure levels set via SSO.",
                    },
                    "number": {"attribute": "participant_kv_number"},
                    "structure_levels": [
                        {
                            "attribute": "kv_structure",
                            "default": "structure1",
                        }
                    ],
                    "groups": [
                        {
                            "attribute": "kv_group_attribute",
                            "default": "not_a_group",
                        }
                    ],
                    "vote_weight": {
                        "attribute": "kv_vw",
                        "default": "1.000000",
                    },
                    "present": {"attribute": "kv_presence", "default": "True"},
                },
            },
        ]
        self.organization["saml_attr_mapping"]["meeting_mappers"] = self.meeting_mappers  # type: ignore
        self.create_meeting()
        self.create_meeting(4)
        self.set_models(
            {
                "organization/1": self.organization,
                "group/1": {"external_id": "Default"},
                "group/2": {"external_id": "Delegates"},
                "group/3": {"external_id": "Admin"},
                "group/4": {"external_id": "Default"},
                "group/5": {"external_id": "Delegates"},
                "group/6": {"external_id": "Admin"},
                "meeting/1": {"external_id": "Landtag", "default_group_id": 1},
                "meeting/4": {"external_id": "Kreistag", "default_group_id": 4},
                "user/1": {"saml_id": "admin_saml"},
            }
        )

    def test_create_user_with_multi_membership(self) -> None:
        """
        Shows:
            * generally works for multiple matching mappers on different meetings
            * if default for 'groups' doesn't resolve, default group of that meeting is used
        """
        response = self.request(
            "user.save_saml_account",
            {
                "username": ["111"],
                "member_number": "LV_Königholz",
                "email": "holzi@holz.de",
                "participant_number": "MG_1254",
                "idp_group_attribute": "Delegates",
                "kv_member_number": "KV_Könighols",
                "kv_email": "hols@holz.de",
                "participant_kv_number": "MG_1254",
                "idp_kv_group_attribute": "Delegates",
                "kv_structure": "structure2",
                "idp_commentary": "normal data used",
            },
        )
        self.assert_status_code(response, 200)
        self.app.logger.warning.assert_called_with(  # type: ignore
            "save_saml_account found no group in meeting 'Kreistag' for ['not_a_group'], but used default_group of meeting"
        )
        self.assert_model_exists(
            "user/2",
            {
                "saml_id": "111",
                "username": "111",
                "email": "holzi@holz.de",
                "meeting_user_ids": [1, 2],
                "meeting_ids": [1, 4],
                "is_present_in_meeting_ids": [1, 4],
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "user_id": 2,
                "meeting_id": 1,
                "group_ids": [2],
                "structure_level_ids": [1],
                "vote_weight": "1.000000",
                "number": "MG_1254",
                "comment": "normal data used",
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "user_id": 2,
                "group_ids": [4],
                "meeting_id": 4,
                "comment": "normal data used",
                "structure_level_ids": [2],
                "vote_weight": "1.000000",
                "number": "MG_1254",
            },
        )
        self.assert_model_exists(
            "group/2", {"meeting_user_ids": [1], "external_id": "Delegates"}
        )
        self.assert_model_exists(
            "structure_level/1",
            {"meeting_user_ids": [1], "name": "structure1"},
        )
        self.assert_model_exists(
            "structure_level/2",
            {"meeting_user_ids": [2], "name": "structure2"},
        )

    def test_create_user_meeting_not_exists(self) -> None:
        """
        Shows: if meeting does not exist error is logged.
        """
        self.meeting_mappers[0]["external_id"] = "Bundestag"
        del self.meeting_mappers[1]
        self.set_models({"organization/1": self.organization})
        response = self.request(
            "user.save_saml_account",
            {
                "username": ["111"],
                "member_number": "LV_Königholz",
                "email": "holzi@holz.de",
                "participant_number": "MG_1254",
                "idp_group_attribute": "Delegates",
                "kv_member_number": "KV_Könighols",
                "kv_email": "hols@holz.de",
                "participant_kv_number": "MG_1254",
                "kv_group_attribute": "Delegates",
                "kv_structure": "structure2",
            },
        )
        self.assert_status_code(response, 200)
        self.app.logger.warning.assert_called_with(  # type: ignore
            "save_saml_account found no meetings for 1 meetings with external_ids ['Bundestag']"
        )
        self.assert_model_exists(
            "user/2",
            {
                "saml_id": "111",
                "username": "111",
                "meeting_user_ids": None,
                "meeting_ids": None,
            },
        )
        self.assert_model_not_exists("meeting_user/1")
        self.assert_model_not_exists("structure_level/1")

    def test_create_user_with_multi_membership_multi(self) -> None:
        """
        Shows:
            * group and structure levels can be multiple values in concatenated, comma separated string list for:
                * default values
                * saml datas values
            * multiple values can be repeated
        """
        self.meeting_mappers[1]["mappings"]["groups"] = [  # type: ignore
            {
                "attribute": "use_default",
                "default": "Default, Delegates, Delegates",
            }
        ]
        self.set_models({"organization/1": self.organization})
        # TODO test Default on same meeting as attribute with 2 mappers
        # TODO multiple same attributes over 2 mappers
        response = self.request(
            "user.save_saml_account",
            {
                "username": ["111"],
                "member_number": "LV_Königholz",
                "email": "holzi@holz.de",
                "participant_number": "MG_1254",
                "idp_group_attribute": "Delegates, Admin, Delegates",
                "kv_member_number": "KV_Könighols",
                "participant_kv_number": "MG_1254",
                "idp_kv_group_attribute": "Delegates",
                "kv_structure": "structure2",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "saml_id": "111",
                "username": "111",
                "meeting_user_ids": [1, 2],
                "meeting_ids": [1, 4],
            },
        )
        self.assert_model_exists(
            "meeting_user/1", {"user_id": 2, "group_ids": [2, 3], "meeting_id": 1}
        )
        self.assert_model_exists(
            "meeting_user/2", {"user_id": 2, "group_ids": [4, 5], "meeting_id": 4}
        )
        self.assert_model_exists(
            "group/2", {"meeting_user_ids": [1], "external_id": "Delegates"}
        )
        self.assert_model_exists(
            "structure_level/1",
            {"meeting_user_ids": [1], "name": "structure1"},
        )
        self.assert_model_exists(
            "structure_level/2",
            {"meeting_user_ids": [2], "name": "structure2"},
        )

    def test_create_user_with_multi_membership_not_matching(self) -> None:
        """
        shows:
        * matching only one mapper -> creating only one meeting user
        """
        response = self.request(
            "user.save_saml_account",
            {
                "username": ["111"],
                "member_number": "LV_Königholz",
                "email": "holzi@holz.de",
                "participant_number": "MG_1254",
                "idp_group_attribute": "Delegates",
                "kv_member_number": "LV_Königholz",
                "kv_email": "hols@holz.de",
                "participant_kv_number": "MG_1254",
                "idp_kv_group_attribute": "Delegates",
                "kv_structure": "structure2",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "saml_id": "111",
                "username": "111",
                "meeting_user_ids": [1],
                "meeting_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/1", {"user_id": 2, "group_ids": [2], "meeting_id": 1}
        )
        self.assert_model_exists(
            "group/2", {"meeting_user_ids": [1], "external_id": "Delegates"}
        )
        self.assert_model_exists(
            "structure_level/1",
            {"meeting_user_ids": [1], "name": "structure1"},
        )
        self.assert_model_not_exists("structure_level/2")

    def test_create_user_only_one_sl_exists(self) -> None:
        """Shows: no errors if one structure level exists and the other doesn't. Latter being created."""
        self.create_model("structure_level/1", {"name": "structure1", "meeting_id": 1})
        response = self.request(
            "user.save_saml_account",
            {
                "username": ["111"],
                "member_number": "LV_Königholz",
                "email": "holzi@holz.de",
                "participant_number": "MG_1254",
                "idp_group_attribute": "Delegates",
                "kv_member_number": "KV_Könighols",
                "kv_email": "hols@holz.de",
                "participant_kv_number": "MG_1254",
                "idp_kv_group_attribute": "Delegates",
                "kv_structure": "structure2",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "saml_id": "111",
                "username": "111",
                "meeting_user_ids": [1, 2],
                "meeting_ids": [1, 4],
            },
        )
        self.assert_model_exists(
            "meeting_user/1", {"user_id": 2, "group_ids": [2], "meeting_id": 1}
        )
        self.assert_model_exists(
            "group/2", {"meeting_user_ids": [1], "external_id": "Delegates"}
        )
        self.assert_model_exists(
            "structure_level/1",
            {"meeting_user_ids": [1], "name": "structure1"},
        )
        self.assert_model_exists(
            "structure_level/2",
            {"meeting_user_ids": [2], "name": "structure2"},
        )

    def test_create_user_mapping_no_mapper(self) -> None:
        del self.organization["saml_attr_mapping"]["meeting_mappers"]  # type: ignore
        self.set_models({"organization/1": self.organization})
        response = self.request(
            "user.save_saml_account",
            {
                "username": ["111"],
                "member_number": "LV_Königholz",
                "email": "holzi@holz.de",
                "participant_number": "MG_1254",
                "idp_group_attribute": "Delegates",
                "kv_member_number": "KV_Könighols",
                "kv_email": "hols@holz.de",
                "participant_kv_number": "MG_1254",
                "idp_kv_group_attribute": "Delegates",
                "kv_structure": "structure2",
                "kv_presence": "True",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "saml_id": "111",
                "username": "111",
            },
        )
        self.assert_model_not_exists("meeting_user/1")
        self.assert_model_not_exists("structure_level/1")

    def test_create_user_mapping_no_mapping(self) -> None:
        del self.meeting_mappers[0]["mappings"]
        del self.meeting_mappers[1]
        self.set_models({"organization/1": self.organization})
        response = self.request(
            "user.save_saml_account",
            {
                "username": ["111"],
                "member_number": "LV_Königholz",
                "email": "holzi@holz.de",
                "participant_number": "MG_1254",
                "idp_group_attribute": "Delegates",
                "kv_member_number": "KV_Könighols",
                "kv_email": "hols@holz.de",
                "participant_kv_number": "MG_1254",
                "idp_kv_group_attribute": "Delegates",
                "kv_structure": "structure2",
                "kv_presence": "True",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "saml_id": "111",
                "username": "111",
            },
        )
        self.assert_model_not_exists("meeting_user/1")
        self.assert_model_not_exists("structure_level/1")

    def test_create_user_mapping_one_meeting_twice(self) -> None:
        self.meeting_mappers[1]["external_id"] = "Landtag"
        self.meeting_mappers[1]["mappings"]["groups"] = [  # type: ignore
            {
                "attribute": "use_default",
                "default": "Default",
            }
        ]
        self.set_models({"organization/1": self.organization})
        response = self.request(
            "user.save_saml_account",
            {
                "username": ["111"],
                "member_number": "LV_Königholz",
                "email": "holzi@holz.de",
                "participant_number": "MG_1254",
                "idp_group_attribute": "Delegates",
                "kv_member_number": "KV_Könighols",
                "kv_email": "hols@holz.de",
                "participant_kv_number": "MG_1254",
                "idp_kv_group_attribute": "Delegates",
                "kv_structure": "structure2",
                "kv_presence": "True",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "saml_id": "111",
                "username": "111",
                "meeting_user_ids": [1],
                "meeting_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/1", {"user_id": 2, "group_ids": [1, 2], "meeting_id": 1}
        )
        self.assert_model_exists(
            "group/1", {"meeting_user_ids": [1], "external_id": "Default"}
        )
        self.assert_model_exists(
            "group/2", {"meeting_user_ids": [1], "external_id": "Delegates"}
        )
        self.assert_model_exists(
            "structure_level/1",
            {"meeting_user_ids": [1], "name": "structure1"},
        )
        self.assert_model_exists(
            "structure_level/2",
            {"meeting_user_ids": [1], "name": "structure2"},
        )

    def test_update_user_with_default_membership(self) -> None:
        self.meeting_mappers[1]["conditions"] = [
            {"attribute": "yes", "condition": ".*"}
        ]
        self.meeting_mappers[1]["mappings"]["groups"][0]["default"] = "Delegates"  # type: ignore
        self.set_models({"organization/1": self.organization})
        response = self.request(
            "user.save_saml_account", {"username": ["admin_saml"], "yes": "to_all"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "saml_id": "admin_saml",
                "username": "admin",
                "meeting_user_ids": [1],
                "meeting_ids": [4],
            },
        )
        self.assert_model_exists(
            "meeting_user/1", {"user_id": 1, "group_ids": [5], "meeting_id": 4}
        )
        self.assert_model_exists(
            "group/5", {"meeting_user_ids": [1], "external_id": "Delegates"}
        )

    # def test_update_user_existing_member_in_group(self) -> None:
    #     """user created and logged in"""
    #     self.set_user_groups(1, [2])
    #     response = self.request("user.save_saml_account", {"username": ["admin_saml"]})
    #     self.assert_status_code(response, 200)
    #     self.assert_model_exists(
    #         "user/1",
    #         {
    #             "saml_id": "admin_saml",
    #             "username": "admin",
    #             "meeting_user_ids": [1],
    #             "meeting_ids": [1],
    #         },
    #     )
    #     self.assert_model_exists(
    #         "meeting_user/1", {"user_id": 1, "group_ids": [2], "meeting_id": 1}
    #     )
    #     self.assert_model_exists(
    #         "group/2", {"meeting_user_ids": [1], "external_id": "Delegates"}
    #     )

    def test_update_user_existing_member_in_group(self) -> None:
        """users meeting user updated without changing group 2 adding group 5 and structure level 2 created sl 1 left untouched"""
        # TODO ich denke ich muss hier noch mal pro meeting user ausschließen, dass nichts verändert wird bei not allowed update
        self.meeting_mappers[0]["allow_update"] = "False"
        self.set_models({"organization/1": self.organization})
        self.set_user_groups(1, [2])
        self.set_models(
            {
                "structure_level/1": {
                    "name": "structure1",
                    "meeting_user_ids": [1],
                    "meeting_id": 1,
                }
            }
        )
        self.update_model("meeting_user/1", {"structure_level_ids": [1]})
        response = self.request(
            "user.save_saml_account",
            {
                "username": ["admin_saml"],
                "member_number": "LV_Königholz",
                "email": "holzi@holz.de",
                "participant_number": "MG_1254",
                "idp_group_attribute": "Delegates",
                "kv_member_number": "KV_Könighols",
                "kv_email": "hols@holz.de",
                "participant_kv_number": "MG_1254",
                "kv_group_attribute": "Delegates",
                "kv_structure": "structure2",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "saml_id": "admin_saml",
                "username": "admin",
                "meeting_user_ids": [1, 2],
                "meeting_ids": [1, 4],
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "user_id": 1,
                "group_ids": [2],
                "meeting_id": 1,
                "structure_level_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "user_id": 1,
                "group_ids": [5],
                "meeting_id": 4,
                "structure_level_ids": [2],
            },
        )
        self.assert_model_exists(
            "group/2", {"meeting_user_ids": [1], "external_id": "Delegates"}
        )
        self.assert_model_exists(
            "structure_level/1", {"name": "structure1", "meeting_user_ids": [1]}
        )
        self.assert_model_exists(
            "structure_level/2", {"name": "structure2", "meeting_user_ids": [2]}
        )
        self.assert_model_not_exists("structure_level/3")

    def test_update_user_existing_member_not_allowed(self) -> None:
        # TODO hier gibt es noch Konflikte mit dem oberen Test
        """users meeting user updated without changing group 2 adding group 5 and structure level 2 and 3 created sl 1 left untouched"""
        self.set_user_groups(1, [2])
        self.set_models(
            {
                "structure_level/1": {
                    "name": "structure1",
                    "meeting_user_ids": [1],
                    "meeting_id": 1,
                }
            }
        )
        self.update_model("meeting_user/1", {"structure_level_ids": [1]})
        response = self.request(
            "user.save_saml_account",
            {
                "username": ["admin_saml"],
                "member_number": "LV_Königholz",
                "email": "holzi@holz.de",
                "participant_number": "MG_1254",
                "idp_group_attribute": "Delegates",
                "kv_member_number": "KV_Könighols",
                "kv_email": "hols@holz.de",
                "participant_kv_number": "MG_1254",
                "kv_group_attribute": "Delegates",
                "kv_structure": "structure2",
                "structure": "structure2",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "saml_id": "admin_saml",
                "username": "admin",
                "meeting_user_ids": [1, 2],
                "meeting_ids": [1, 4],
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "user_id": 1,
                "group_ids": [2],
                "meeting_id": 1,
                "structure_level_ids": [1, 2],
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "user_id": 1,
                "group_ids": [5],
                "meeting_id": 4,
                "structure_level_ids": [3],
            },
        )
        self.assert_model_exists(
            "group/2", {"meeting_user_ids": [1], "external_id": "Delegates"}
        )
        self.assert_model_exists(
            "structure_level/1", {"name": "structure1", "meeting_user_ids": [1]}
        )
        self.assert_model_exists(
            "structure_level/2", {"name": "structure2", "meeting_user_ids": [1]}
        )
        self.assert_model_exists(
            "structure_level/3", {"name": "structure2", "meeting_user_ids": [2]}
        )

    def test_update_user_add_group_to_existing_groups(self) -> None:
        """group added, user created and logged in"""
        self.set_user_groups(1, [1, 3])
        response = self.request(
            "user.save_saml_account",
            {
                "username": ["admin_saml"],
                "member_number": "LV_Königholz",
                "email": "holzi@holz.de",
                "participant_number": "MG_1254",
                "idp_group_attribute": "Delegates",
                "kv_member_number": "KV_Könighols",
                "kv_email": "hols@holz.de",
                "participant_kv_number": "MG_1254",
                "kv_group_attribute": "Delegates",
                "kv_structure": "structure2",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "saml_id": "admin_saml",
                "username": "admin",
                "meeting_user_ids": [1, 2],
                "meeting_ids": [1, 4],
            },
        )
        self.assert_model_exists(
            "meeting_user/1", {"user_id": 1, "group_ids": [1, 3, 2], "meeting_id": 1}
        )
        self.assert_model_exists(
            "meeting_user/2", {"user_id": 1, "group_ids": [5], "meeting_id": 4}
        )
        self.assert_model_exists(
            "group/2", {"meeting_user_ids": [1], "external_id": "Delegates"}
        )
