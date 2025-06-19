from typing import Any

from openslides_backend.action.mixins.import_mixins import BaseImportAction, ImportState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase

from .test_account_json_upload import AccountJsonUploadForUseInImport


class AccountJsonImport(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "organization/1": {"gender_ids": [1, 2, 3, 4]},
                "gender/1": {"name": "male"},
                "gender/2": {"name": "female"},
                "gender/3": {"name": "diverse"},
                "gender/4": {"name": "non-binary"},
                "import_preview/2": {
                    "state": ImportState.DONE,
                    "name": "account",
                    "result": {
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "username": {
                                        "value": "jonny",
                                        "info": ImportState.DONE,
                                    },
                                    "first_name": "Testy",
                                },
                            },
                        ],
                    },
                },
                "import_preview/3": {
                    "state": ImportState.DONE,
                    "name": "account",
                    "result": {
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "username": {
                                        "value": "TestyTester",
                                        "info": ImportState.DONE,
                                    },
                                    "first_name": "Testy",
                                    "last_name": "Tester",
                                    "email": {
                                        "value": "email@test.com",
                                        "info": ImportState.DONE,
                                    },
                                    "gender_id": {
                                        "value": 1,
                                        "info": ImportState.DONE,
                                    },
                                },
                            },
                        ],
                    },
                },
                "import_preview/4": {
                    "state": ImportState.ERROR,
                    "name": "account",
                    "result": {
                        "rows": [
                            {
                                "state": ImportState.ERROR,
                                "messages": ["test"],
                                "data": {
                                    "gender_id": {
                                        "value": 1,
                                        "info": ImportState.DONE,
                                    }
                                },
                            },
                        ],
                    },
                },
                "import_preview/5": {"result": None},
                "user/2": {
                    "username": "test",
                    "default_password": "secret",
                    "password": "secret",
                },
                "import_preview/6": {
                    "state": ImportState.WARNING,
                    "name": "account",
                    "result": {
                        "rows": [
                            {
                                "state": ImportState.DONE,
                                "messages": [],
                                "data": {
                                    "id": 2,
                                    "username": {
                                        "value": "test",
                                        "info": ImportState.DONE,
                                        "id": 2,
                                    },
                                    "saml_id": {
                                        "value": "12345",
                                        "info": ImportState.DONE,
                                    },
                                    "default_password": {
                                        "value": "",
                                        "info": ImportState.WARNING,
                                    },
                                },
                            },
                        ],
                    },
                },
            }
        )

    def test_import_username_and_create(self) -> None:
        response = self.request("account.import", {"id": 2, "import": True})
        self.assert_status_code(response, 200)
        user = self.assert_model_exists(
            "user/3",
            {"username": "jonny", "first_name": "Testy"},
        )
        assert user.get("default_password")
        assert user.get("password")
        self.assert_model_not_exists("import_preview/2")

    def test_import_abort(self) -> None:
        response = self.request("account.import", {"id": 2, "import": False})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("import_preview/2")
        self.assert_model_not_exists("user/3")

    def test_import_wrong_import_preview(self) -> None:
        response = self.request("account.import", {"id": 5, "import": True})
        self.assert_status_code(response, 400)
        assert (
            "Wrong id doesn't point on account import data." in response.json["message"]
        )

    def test_import_username_and_update(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "username": "user1",
                },
                "import_preview/7": {
                    "state": ImportState.DONE,
                    "name": "account",
                    "result": {
                        "rows": [
                            {
                                "state": ImportState.DONE,
                                "messages": [],
                                "data": {
                                    "id": 1,
                                    "username": {
                                        "value": "user1",
                                        "info": ImportState.DONE,
                                        "id": 1,
                                    },
                                    "first_name": "Testy",
                                    "gender_id": {
                                        "value": 4,
                                        "info": ImportState.DONE,
                                    },
                                },
                            },
                        ],
                    },
                },
            }
        )
        response = self.request("account.import", {"id": 7, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"first_name": "Testy", "gender_id": 4})

    def test_ignore_unknown_gender(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "username": "user1",
                },
                "import_preview/7": {
                    "state": ImportState.DONE,
                    "name": "account",
                    "result": {
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [
                                    "GenderId '5' is not in the allowed gender list."
                                ],
                                "data": {
                                    "id": 1,
                                    "username": {
                                        "value": "user1",
                                        "info": ImportState.DONE,
                                        "id": 1,
                                    },
                                    "gender_id": {
                                        "value": 5,
                                        "info": ImportState.WARNING,
                                    },
                                },
                            },
                        ],
                    },
                },
            }
        )
        response = self.request("account.import", {"id": 7, "import": True})
        self.assert_status_code(response, 200)
        user = self.assert_model_exists("user/1")
        assert user.get("gender_id") is None

    def test_import_names_and_email_and_create(self) -> None:
        response = self.request("account.import", {"id": 3, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/3",
            {
                "username": "TestyTester",
                "first_name": "Testy",
                "gender_id": 1,
                "last_name": "Tester",
                "email": "email@test.com",
            },
        )

    def get_import_preview_data(
        self, number: int, row_state: ImportState, data: dict[str, Any]
    ) -> dict[str, Any]:
        def get_import_state() -> ImportState:
            """Precondition: There is only 1 row(_state)"""
            if row_state == ImportState.ERROR:
                return row_state
            if BaseImportAction.count_warnings_in_payload(data):
                return ImportState.WARNING
            else:
                return ImportState.DONE

        return {
            f"import_preview/{number}": {
                "state": get_import_state(),
                "name": "account",
                "result": {
                    "rows": [
                        {
                            "state": row_state,
                            "messages": [],
                            "data": data,
                        },
                    ],
                },
            }
        }

    def test_import_with_saml_id(self) -> None:
        self.set_models(
            self.get_import_preview_data(
                7,
                ImportState.NEW,
                {"saml_id": {"value": "testsaml", "info": ImportState.NEW}},
            )
        )
        response = self.request("account.import", {"id": 7, "import": True})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Invalid JsonUpload data: The data from json upload must contain a valid username object",
            response.json["message"],
        )

    def test_import_saml_id_error_new_and_saml_id_exists(self) -> None:
        """Set saml_id 'testsaml' to user 1, add the import user 1 will be
        found and the import should result in an error."""
        self.set_models(
            {
                "user/1": {"saml_id": "testsaml"},
                **self.get_import_preview_data(
                    6,
                    ImportState.NEW,
                    {
                        "username": {"value": "testuser", "info": ImportState.NEW},
                        "saml_id": {"value": "testsaml", "info": ImportState.NEW},
                    },
                ),
            }
        )
        response = self.request("account.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: saml_id 'testsaml' found in different id (1 instead of None)"
        ]

    def test_import_done_error_missing_user(self) -> None:
        self.set_models(
            {
                **self.get_import_preview_data(
                    6,
                    ImportState.DONE,
                    {
                        "username": {
                            "value": "XYZ",
                            "info": ImportState.DONE,
                            "id": 78,
                        },
                        "saml_id": {"value": "testsaml", "info": ImportState.NEW},
                        "first_name": "Hugo",
                        "id": 78,
                    },
                ),
            }
        )
        response = self.request("account.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: account 78 not found anymore for updating account 'XYZ'."
        ]

    def test_import_error_state_done_missing_username(self) -> None:
        self.set_models(
            self.get_import_preview_data(
                6,
                ImportState.DONE,
                {
                    "first_name": "Testy",
                },
            )
        )
        response = self.request("account.import", {"id": 6, "import": True})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Invalid JsonUpload data: The data from json upload must contain a valid username object",
            response.json["message"],
        )

    def test_import_error_state_done_missing_user_in_db(self) -> None:
        self.set_models(
            self.get_import_preview_data(
                6,
                ImportState.DONE,
                {
                    "first_name": "Testy",
                    "username": {
                        "value": "fred",
                        "info": ImportState.DONE,
                        "id": 111,
                    },
                    "id": 111,
                },
            )
        )
        response = self.request("account.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: account 111 not found anymore for updating account 'fred'."
        ]

    def test_import_error_state_done_search_data_error(self) -> None:
        self.set_models(
            {
                "import_preview/7": {
                    "state": ImportState.DONE,
                    "name": "account",
                    "result": {
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "username": {
                                        "value": "durban",
                                        "info": ImportState.DONE,
                                    }
                                },
                            },
                            {
                                "state": ImportState.DONE,
                                "messages": [],
                                "data": {
                                    "username": {
                                        "value": "durban",
                                        "info": ImportState.DONE,
                                    }
                                },
                            },
                        ],
                    },
                }
            }
        )
        response = self.request("account.import", {"id": 7, "import": True})
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.ERROR
        for i in range(2):
            entry = result["rows"][i]
            assert entry["state"] == ImportState.ERROR
            assert entry["messages"] == [
                "Error: username 'durban' is duplicated in import."
            ]

    def test_import_error_state_done_not_matching_ids(self) -> None:
        self.set_models(
            {
                "user/8": {"username": "user8"},
                **self.get_import_preview_data(
                    6,
                    ImportState.DONE,
                    {
                        "id": 5,
                        "first_name": "Testy",
                        "username": {
                            "value": "user8",
                            "info": ImportState.DONE,
                            "id": 5,
                        },
                    },
                ),
            }
        )
        response = self.request("account.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: username 'user8' found in different id (8 instead of 5)"
        ]

    def test_import_error_state_import_preview4(self) -> None:
        response = self.request("account.import", {"id": 4, "import": True})
        self.assert_status_code(response, 400)
        assert response.json["message"] == "Error in import. Data will not be imported."
        self.assert_model_exists("import_preview/4")

    def test_import_no_permission(self) -> None:
        self.base_permission_test({}, "account.import", {"id": 2, "import": True})

    def test_import_permission(self) -> None:
        self.base_permission_test(
            {},
            "account.import",
            {"id": 2, "import": True},
            OrganizationManagementLevel.CAN_MANAGE_USERS,
        )


class AccountJsonImportWithIncludedJsonUpload(AccountJsonUploadForUseInImport):
    def test_upload_import_with_generated_usernames_okay(self) -> None:
        self.json_upload_saml_id_new()
        response_import = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        self.assert_model_exists(
            "user/35",
            {
                "username": "test_saml_id2",
                "saml_id": "test_saml_id",
                "default_password": "",
                "can_change_own_password": False,
                "default_vote_weight": "1.000000",
                "organization_id": 1,
                "is_physical_person": True,
            },
        )
        user36 = self.assert_model_exists(
            "user/36",
            {
                "username": "test_saml_id1",
                "saml_id": None,
                "can_change_own_password": True,
                "default_vote_weight": "1.000000",
            },
        )
        assert user36["default_password"]
        assert user36["password"]

        user37 = self.assert_model_exists(
            "user/37",
            {
                "username": "test_saml_id21",
                "saml_id": None,
                "can_change_own_password": True,
                "default_vote_weight": "1.000000",
            },
        )
        assert user37["default_password"]
        assert user37["password"]

        self.assert_model_not_exists("import_preview/1")

    def test_upload_import_with_generated_usernames_error_username(self) -> None:
        self.json_upload_saml_id_new()
        self.set_models({"user/33": {"username": "test_saml_id21"}})
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][2]["state"] == ImportState.ERROR
        assert response.json["results"][0][0]["rows"][2]["messages"] == [
            "Error: row state expected to be 'done', but it is 'new'."
        ]
        assert response.json["results"][0][0]["rows"][2]["data"]["username"] == {
            "info": ImportState.ERROR,
            "value": "test_saml_id21",
        }
        self.assert_model_not_exists("user/35")
        self.assert_model_not_exists("user/36")
        self.assert_model_not_exists("user/37")
        self.assert_model_exists("import_preview/1")

    def test_json_upload_set_saml_id_in_existing_account(self) -> None:
        self.json_upload_set_saml_id_in_existing_account()
        response_import = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "test",
                "saml_id": "test_saml_id",
                "default_password": "",
                "can_change_own_password": False,
                "password": "",
                "default_vote_weight": "2.300000",
            },
        )
        self.assert_model_not_exists("import_preview/1")

    def test_json_upload_update_saml_id_in_existing_account(self) -> None:
        self.json_upload_update_saml_id_in_existing_account()
        response_import = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "test",
                "saml_id": "new_one",
                "default_vote_weight": "2.300000",
            },
        )
        self.assert_model_not_exists("import_preview/1")

    def test_json_upload_names_and_email_find_username_error(self) -> None:
        self.json_upload_names_and_email_find_username()
        self.set_models({"user/34": {"username": "test34"}})
        response_import = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        row = response_import.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Error: account 34 not found anymore for updating account 'test'."
        ]
        assert row["data"] == {
            "id": 34,
            "email": {"value": "test@ntvtn.de", "info": ImportState.DONE},
            "username": {"id": 34, "info": "error", "value": "test"},
            "last_name": {"value": "Mustermann", "info": ImportState.DONE},
            "first_name": {"value": "Max", "info": ImportState.DONE},
            "default_password": {"info": "done", "value": "new default password"},
        }

    def test_json_upload_names_and_email_find_username_ok(self) -> None:
        self.json_upload_names_and_email_find_username()
        response_import = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        row = response_import.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["messages"] == []
        assert row["data"] == {
            "id": 34,
            "email": {"value": "test@ntvtn.de", "info": ImportState.DONE},
            "username": {"id": 34, "info": "done", "value": "test"},
            "last_name": {"value": "Mustermann", "info": ImportState.DONE},
            "first_name": {"value": "Max", "info": ImportState.DONE},
            "default_password": {"info": "done", "value": "new default password"},
        }

    def test_json_upload_names_and_email_generate_username(self) -> None:
        self.json_upload_names_and_email_generate_username()
        response_import = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        row = response_import.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.NEW
        assert row["messages"] == []
        self.assert_model_exists(
            "user/35",
            {
                "id": 35,
                "username": "MaxMustermann1",
                "last_name": "Mustermann",
                "first_name": "Max",
                "organization_id": 1,
                "is_physical_person": True,
                "default_vote_weight": "1.000000",
                "can_change_own_password": True,
            },
        )

    def test_json_upload_with_complicated_names(self) -> None:
        self.json_upload_with_complicated_names()
        response_import = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        rows = response_import.json["results"][0][0]["rows"]
        for i in range(5):
            number = f"{i}" if i else ""
            assert rows[i]["state"] == ImportState.NEW
            assert rows[i]["messages"] == []
            assert rows[i]["data"]["username"] == {
                "info": ImportState.GENERATED,
                "value": "OneTwoThree" + number,
            }

    def test_json_upload_generate_default_password(self) -> None:
        self.json_upload_generate_default_password()
        response_import = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        row = response_import.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.NEW
        assert row["messages"] == []
        user2 = self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "username": "test",
                "organization_id": 1,
                "is_physical_person": True,
                "default_vote_weight": "1.000000",
                "can_change_own_password": True,
            },
        )
        assert user2["default_password"]
        assert user2["password"]

    def test_json_upload_username_10_saml_id_11_error(self) -> None:
        self.json_upload_username_10_saml_id_11()
        self.set_models({"user/11": {"saml_id": "saml_id10"}})
        response_import = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        row = response_import.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Because this account is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Error: saml_id 'saml_id10' found in different id (11 instead of 10)",
        ]
        assert row["data"] == {
            "id": 10,
            "saml_id": {"info": "error", "value": "saml_id10"},
            "username": {"id": 10, "info": "done", "value": "user10"},
            "default_password": {"info": "warning", "value": ""},
        }

    def test_json_upload_username_username_and_saml_id_found_and_deleted_error(
        self,
    ) -> None:
        self.json_upload_username_username_and_saml_id_found()
        self.request("user.delete", {"id": 11})
        assert self.assert_model_deleted("user/11")
        response_import = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        row = response_import.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Error: account 11 not found anymore for updating account 'user11'."
        ]
        assert row["data"] == {
            "id": 11,
            "saml_id": {"info": "done", "value": "saml_id11"},
            "username": {"id": 11, "info": ImportState.ERROR, "value": "user11"},
            "default_vote_weight": {"value": "11.000000", "info": ImportState.DONE},
        }

    def test_json_upload_update_multiple_users_okay(self) -> None:
        self.json_upload_multiple_users()
        response_import = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "saml_id": "test_saml_id2",
                "username": "user2",
                "default_password": "",
                "default_vote_weight": "2.345678",
                "password": "",
                "can_change_own_password": False,
            },
        )
        self.assert_model_exists(
            "user/3",
            {
                "id": 3,
                "saml_id": "saml3",
                "username": "user3",
                "default_password": "",
                "default_vote_weight": "3.345678",
                "can_change_own_password": False,
            },
        )
        self.assert_model_exists(
            "user/4",
            {
                "id": 4,
                "username": "user4",
                "email": "mlk@america.com",
                "first_name": "Martin",
                "last_name": "Luther King",
                "default_password": "secret",
                "default_vote_weight": "4.345678",
                "can_change_own_password": True,
            },
        )
        self.assert_model_exists(
            "user/5",
            {
                "id": 5,
                "saml_id": "saml5",
                "username": "new_user5",
                "default_password": "",
                "default_vote_weight": "5.345678",
                "can_change_own_password": False,
            },
        )
        self.assert_model_exists(
            "user/6",
            {
                "id": 6,
                "saml_id": "new_saml6",
                "username": "new_saml6",
                "default_password": "",
                "default_vote_weight": "6.345678",
                "can_change_own_password": False,
            },
        )
        self.assert_model_exists(
            "user/7",
            {
                "id": 7,
                "username": "JoanBaez7",
                "first_name": "Joan",
                "last_name": "Baez7",
                "default_vote_weight": "7.345678",
                "can_change_own_password": True,
            },
        )

    def test_json_upload_update_multiple_users_all_error(self) -> None:
        self.json_upload_multiple_users()
        self.request("user.delete", {"id": 2})
        self.set_models(
            {
                "user/10": {"username": "doubler3", "saml_id": "saml3"},
                "user/4": {"username": "user4_married"},
                "user/11": {"username": "new_user_5", "saml_id": "saml5"},
                "user/12": {"username": "doubler6", "saml_id": "new_saml6"},
                "user/13": {"username": "JoanBaez7"},
            },
        )
        response_import = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        assert (result := response_import.json["results"][0][0])[
            "state"
        ] == ImportState.ERROR
        row = result["rows"][0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Because this account is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Error: account 2 not found anymore for updating account 'user2'.",
        ]
        assert row["data"] == {
            "id": 2,
            "saml_id": {"info": ImportState.NEW, "value": "test_saml_id2"},
            "username": {"id": 2, "info": ImportState.ERROR, "value": "user2"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "default_vote_weight": {"value": "2.345678", "info": ImportState.DONE},
        }

        row = result["rows"][1]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Because this account is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Error: saml_id 'saml3' is duplicated in import.",
        ]
        assert row["data"] == {
            "id": 3,
            "saml_id": {"info": ImportState.ERROR, "value": "saml3"},
            "username": {"id": 3, "info": ImportState.DONE, "value": "user3"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "default_vote_weight": {"value": "3.345678", "info": ImportState.DONE},
        }

        row = result["rows"][2]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Error: account 4 not found anymore for updating account 'user4'."
        ]
        assert row["data"] == {
            "id": 4,
            "email": {"value": "mlk@america.com", "info": ImportState.DONE},
            "username": {"id": 4, "info": ImportState.ERROR, "value": "user4"},
            "last_name": {"value": "Luther King", "info": ImportState.DONE},
            "first_name": {"value": "Martin", "info": ImportState.DONE},
            "default_vote_weight": {"value": "4.345678", "info": ImportState.DONE},
        }

        row = result["rows"][3]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Because this account is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Error: saml_id 'saml5' found in different id (11 instead of None)",
        ]
        assert row["data"] == {
            "username": {"info": ImportState.DONE, "value": "new_user5"},
            "saml_id": {"info": ImportState.ERROR, "value": "saml5"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "default_vote_weight": {"value": "5.345678", "info": ImportState.DONE},
        }

        row = result["rows"][4]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Because this account is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Error: saml_id 'new_saml6' found in different id (12 instead of None)",
        ]
        assert row["data"] == {
            "username": {"info": ImportState.GENERATED, "value": "new_saml6"},
            "saml_id": {"info": ImportState.ERROR, "value": "new_saml6"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "default_vote_weight": {"value": "6.345678", "info": ImportState.DONE},
        }

        row = result["rows"][5]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Error: row state expected to be 'done', but it is 'new'."
        ]
        assert row["data"]["username"] == {
            "info": ImportState.ERROR,
            "value": "JoanBaez7",
        }
        assert row["data"]["default_password"]["info"] == ImportState.GENERATED
        assert row["data"]["default_password"]["value"]

    def test_json_upload_wrong_gender(self) -> None:
        self.json_upload_wrong_gender()
        response_import = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        user = self.assert_model_exists("user/2", {"username": "test"})
        assert "gender_id" not in user.keys()

    def test_json_upload_wrong_gender_2(self) -> None:
        self.json_upload_wrong_gender_2()
        response_import = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        user = self.assert_model_exists("user/2", {"username": "test"})
        assert "gender_id" not in user.keys()

    def test_json_upload_legacy_username(self) -> None:
        self.json_upload_legacy_username()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)

    def test_json_upload_update_reference_via_two_attributes(self) -> None:
        self.json_upload_update_reference_via_two_attributes()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "username": "test",
                "saml_id": "old_one",
                "default_vote_weight": "4.500000",
            },
        )

    def test_json_upload_set_member_number_in_existing_accounts(self) -> None:
        self.json_upload_set_member_number_in_existing_accounts()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "username": "test1",
                "member_number": "new_one",
            },
        )
        self.assert_model_exists(
            "user/3",
            {
                "id": 3,
                "username": "test2",
                "saml_id": "samLidman",
                "member_number": "another_new_1",
            },
        )
        self.assert_model_exists(
            "user/4",
            {
                "id": 4,
                "username": "test3",
                "first_name": "Hasan",
                "last_name": "Ame",
                "email": "hasaN.ame@nd.email",
                "member_number": "UGuessedIt",
            },
        )

    def test_json_upload_set_other_matching_criteria_in_existing_account_via_member_number(
        self,
    ) -> None:
        self.json_upload_set_other_matching_criteria_in_existing_account_via_member_number()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "username": "newname",
                "saml_id": "some_other_saml",
                "first_name": "second",
                "last_name": "second_to_last",
                "member_number": "M3MNUM",
                "default_password": "",
                "password": "",
                "email": "a.new@ma.il",
            },
        )

    def test_json_upload_add_member_number(self) -> None:
        self.json_upload_add_member_number()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "username": "test",
                "member_number": "old_one",
                "default_vote_weight": "4.345678",
            },
        )

    def test_json_upload_new_account_with_member_number(self) -> None:
        self.json_upload_new_account_with_member_number()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "username": "newname",
                "saml_id": "some_other_saml",
                "first_name": "second",
                "last_name": "second_to_last",
                "member_number": "M3MNUM",
            },
        )

    def test_json_upload_match_via_member_number_no_username(self) -> None:
        self.json_upload_match_via_member_number_no_username()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "username": "test",
                "member_number": "M3MNUM",
            },
        )

    def test_json_upload_match_via_member_number_no_username_or_other_data(
        self,
    ) -> None:
        self.json_upload_match_via_member_number_no_username_or_other_data()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "username": "test",
                "member_number": "M3MNUM",
            },
        )

    def test_json_upload_set_home_committee(self) -> None:
        self.json_upload_set_home_committee()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"id": 2, "username": "Alice", "home_committee_id": 1, "guest": False},
        )

    def test_json_upload_set_home_committee_and_guest_false(self) -> None:
        self.json_upload_set_home_committee(guest=False)
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"id": 2, "username": "Alice", "home_committee_id": 1, "guest": False},
        )

    def test_json_upload_update_home_committee(self) -> None:
        self.json_upload_update_home_committee()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "username": "Alice",
                "home_committee_id": 2,
                "guest": False,
                "first_name": "alice",
            },
        )

    def test_json_upload_set_guest_to_true(self) -> None:
        self.json_upload_set_guest_to_true()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"id": 2, "username": "Alice", "guest": True},
        )

    def test_json_upload_update_guest_true_without_home_committee(self) -> None:
        self.json_upload_update_guest_true()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"id": 2, "username": "Alice", "guest": True},
        )

    def test_json_upload_update_guest_false_without_home_committee(self) -> None:
        self.json_upload_update_guest_false_without_home_committee()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"id": 2, "username": "Alice", "guest": False},
        )

    def test_json_upload_update_guest_true_with_home_committee(self) -> None:
        self.json_upload_update_guest_true(with_home_committee=True)
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"id": 2, "username": "Alice", "home_committee_id": None, "guest": True},
        )

    def test_json_upload_update_guest_false_with_home_committee(self) -> None:
        self.json_upload_update_guest_false_with_home_committee()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"id": 2, "username": "Alice", "home_committee_id": 1, "guest": False},
        )

    def test_json_upload_update_guest_true_without_home_committee_perms(self) -> None:
        self.json_upload_update_guest_true(
            with_home_committee=True, has_home_committee_perms=False
        )
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"id": 2, "username": "Alice", "first_name": "alice", "guest": None},
        )

    def test_json_upload_update_guest_false_without_home_committee_perms(self) -> None:
        self.json_upload_update_guest_false_without_home_committee_perms()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"id": 2, "username": "Alice", "guest": None},
        )

    def test_json_upload_set_home_committee_no_perms(self) -> None:
        self.json_upload_set_home_committee(has_perm=False)
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "username": "Alice",
            },
        )

    def test_json_upload_set_home_committee_and_guest_false_no_perms(self) -> None:
        self.json_upload_set_home_committee(guest=False, has_perm=False)
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"id": 2, "username": "Alice", "guest": None, "home_committee_id": None},
        )

    def test_json_upload_update_home_committee_no_perms_old(self) -> None:
        self.json_upload_update_home_committee(old_perm=False)
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "username": "Alice",
                "home_committee_id": 1,
            },
        )

    def test_json_upload_update_home_committee_no_perms_both(self) -> None:
        self.json_upload_update_home_committee(old_perm=False, new_perm=False)
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"id": 2, "username": "Alice", "first_name": "alice"},
        )

    def test_json_upload_update_home_committee_and_guest_false_no_perms_new(
        self,
    ) -> None:
        self.json_upload_update_home_committee_and_guest_false_no_perms_new()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"id": 2, "username": "Alice", "guest": None, "home_committee_id": 1},
        )

    def test_json_upload_with_gender_as_orga_admin(self) -> None:
        self.json_upload_with_gender_as_orga_admin()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"id": 2, "username": "man", "gender_id": 1},
        )

    def test_json_upload_multiple_with_same_home_committee(self) -> None:
        self.json_upload_multiple_with_same_home_committee()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"id": 2, "first_name": "Tick", "username": "Huey", "home_committee_id": 1},
        )
        self.assert_model_exists(
            "user/3",
            {
                "id": 3,
                "first_name": "Trick",
                "username": "Dewey",
                "home_committee_id": 1,
            },
        )
        self.assert_model_exists(
            "user/4",
            {
                "id": 4,
                "first_name": "Track",
                "username": "Louie",
                "home_committee_id": 1,
            },
        )

    def test_json_upload_multiple_with_x(self) -> None:
        self.json_upload_multiple_with_x()
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/3",
            {"id": 3, "first_name": "Gustav", "username": "schwante"},
        )
        self.assert_model_exists(
            "user/4",
            {
                "id": 4,
                "first_name": "bib",
                "last_name": "lib",
                "username": "biblib",
            },
        )
        self.assert_model_exists(
            "user/5",
            {
                "id": 5,
                "first_name": "Loki",
                "username": "witz",
                "email": "loki@asen.sk",
            },
        )
