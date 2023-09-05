from typing import Any, Dict

from openslides_backend.action.mixins.import_mixins import ImportMixin, ImportState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase
from .test_account_json_upload import  AccountJsonUploadForUseInImport


class AccountJsonImport(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "action_worker/2": {
                    "state": ImportState.DONE,
                    "result": {
                        "import": "account",
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "username": {
                                        "value": "test",
                                        "info": ImportState.DONE,
                                    },
                                    "first_name": "Testy",
                                },
                            },
                        ],
                    },
                },
                "action_worker/3": {
                    "state": ImportState.DONE,
                    "result": {
                        "import": "account",
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
                                    "email": "email@test.com",
                                    "gender": "male",
                                },
                            },
                        ],
                    },
                },
                "action_worker/4": {
                    "state": ImportState.ERROR,
                    "result": {
                        "import": "account",
                        "rows": [
                            {
                                "state": ImportState.ERROR,
                                "messages": ["test"],
                                "data": {"gender": "male"},
                            },
                        ],
                    },
                },
                "action_worker/5": {"result": None},
                "user/2": {
                    "username": "test",
                    "default_password": "secret",
                    "password": "secret",
                },
                "action_worker/6": {
                    "state": ImportState.WARNING,
                    "result": {
                        "import": "account",
                        "rows": [
                            {
                                "state": ImportState.DONE,
                                "messages": ["test"],
                                "data": {
                                    "username": {
                                        "value": "test",
                                        "info": ImportState.DONE,
                                        "id": 2,
                                    },
                                    "saml_id": {
                                        "value": "12345",
                                        "info": ImportState.DONE,
                                        "id": 2,
                                    },
                                    "default_password": {
                                        "value": "test2",
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
        user2 = self.assert_model_exists(
            "user/2",
            {"username": "test", "first_name": "Testy"},
        )
        assert user2.get("default_password")
        assert user2.get("password")
        self.assert_model_not_exists("action_worker/2")

    def test_import_abort(self) -> None:
        response = self.request("account.import", {"id": 2, "import": False})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("action_worker/2")
        self.assert_model_not_exists("user/2")

    def test_import_wrong_action_worker(self) -> None:
        response = self.request("account.import", {"id": 5, "import": True})
        self.assert_status_code(response, 400)
        assert (
            "Wrong id doesn't point on account import data." in response.json["message"]
        )

    def test_import_username_and_update(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "username": "test",
                },
                "action_worker/6": {
                    "state": ImportState.DONE,
                    "result": {
                        "import": "account",
                        "rows": [
                            {
                                "state": ImportState.DONE,
                                "messages": [],
                                "data": {
                                    "username": {
                                        "value": "test",
                                        "info": ImportState.DONE,
                                        "id": 1,
                                    },
                                    "first_name": "Testy",
                                },
                            },
                        ],
                    },
                },
            }
        )
        response = self.request("account.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/2")
        self.assert_model_exists("user/1", {"first_name": "Testy"})

    def test_import_names_and_email_and_create(self) -> None:
        response = self.request("account.import", {"id": 3, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "TestyTester",
                "first_name": "Testy",
                "gender": "male",
                "last_name": "Tester",
                "email": "email@test.com",
            },
        )

    def get_action_worker_data(
        self, number: int, row_state: ImportState, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        def get_import_state() -> ImportState:
            """Precondition: There is only 1 row(_state)"""
            if row_state == ImportState.ERROR:
                return row_state
            if ImportMixin.count_warnings_in_payload(data):
                return ImportState.WARNING
            else:
                return ImportState.DONE

        return {
            f"action_worker/{number}": {
                "state": get_import_state(),
                "result": {
                    "import": "account",
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
            self.get_action_worker_data(
                7,
                ImportState.NEW,
                {"saml_id": {"value": "testsaml", "info": ImportState.NEW}},
            )
        )
        response = self.request("account.import", {"id": 7, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/3",
            {
                "username": "testsaml",
                "saml_id": "testsaml",
            },
        )

    def test_import_saml_id_error_new_and_saml_id_exists(self) -> None:
        """Set saml_id 'testsaml' to user 1, add the import user 1 will be
        found and the import should result in an error."""
        self.set_models(
            {
                "user/1": {"saml_id": "testsaml"},
                **self.get_action_worker_data(
                    6,
                    ImportState.NEW,
                    {"saml_id": {"value": "testsaml", "info": ImportState.NEW}},
                ),
            }
        )
        response = self.request("account.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: want to create a new user, but saml_id already exists."
        ]

    def test_import_done_with_saml_id(self) -> None:
        self.set_models(
            {
                "user/2": {"username": "test", "saml_id": "testsaml"},
                **self.get_action_worker_data(
                    6,
                    ImportState.DONE,
                    {
                        "saml_id": {"value": "testsaml", "info": ImportState.DONE},
                        "id": 2,
                        "first_name": "Hugo",
                    },
                ),
            }
        )
        response = self.request("account.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "test",
                "saml_id": "testsaml",
                "first_name": "Hugo",
            },
        )

    def test_import_done_error_missing_user(self) -> None:
        self.set_models(
            {
                **self.get_action_worker_data(
                    6,
                    ImportState.DONE,
                    {
                        "saml_id": {"value": "testsaml", "info": ImportState.NEW},
                        "first_name": "Hugo",
                        "id": 2,
                    },
                ),
            }
        )
        response = self.request("account.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == ["Error: want to update, but missing user in db."]

    def test_import_error_at_state_new(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "username": "test",
                },
                **self.get_action_worker_data(
                    6,
                    ImportState.NEW,
                    {
                        "first_name": "Testy",
                    },
                ),
                **self.get_action_worker_data(
                    7,
                    ImportState.NEW,
                    {
                        "first_name": "Testy",
                        "username": {
                            "value": "test",
                            "info": ImportState.DONE,
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
            "Error: Want to create user, but missing username in import data."
        ]

        response = self.request("account.import", {"id": 7, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: want to create a new user, but username already exists."
        ]

    def test_import_error_state_done_missing_username(self) -> None:
        self.set_models(
            self.get_action_worker_data(
                6,
                ImportState.DONE,
                {
                    "first_name": "Testy",
                },
            )
        )
        response = self.request("account.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: Want to update user, but missing username in import data."
        ]

    def test_import_error_state_done_missing_user_in_db(self) -> None:
        self.set_models(
            self.get_action_worker_data(
                6,
                ImportState.DONE,
                {
                    "first_name": "Testy",
                    "username": {"value": "test", "info": ImportState.DONE},
                },
            )
        )
        response = self.request("account.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == ["Error: want to update, but missing user in db."]

    def test_import_error_state_done_search_data_error(self) -> None:
        self.set_models(
            {
                "action_worker/6": {
                    "result": {
                        "import": "account",
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "username": {
                                        "value": "test",
                                        "info": ImportState.DONE,
                                    }
                                },
                            },
                            {
                                "state": ImportState.DONE,
                                "messages": [],
                                "data": {
                                    "username": {
                                        "value": "test",
                                        "info": ImportState.DONE,
                                    }
                                },
                            },
                        ],
                    },
                }
            }
        )
        response = self.request("account.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][1]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: want to update, but found search data are wrong."
        ]

    def test_import_error_state_done_not_matching_ids(self) -> None:
        self.set_models(
            {
                "user/8": {"username": "test"},
                **self.get_action_worker_data(
                    6,
                    ImportState.DONE,
                    {
                        "first_name": "Testy",
                        "username": {
                            "value": "test",
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
            "Error: want to update, but found search data doesn't match."
        ]

    def test_import_error_state_action_worker4(self) -> None:
        response = self.request("account.import", {"id": 4, "import": True})
        self.assert_status_code(response, 400)
        assert response.json["message"] == "Error in import. Data will not be imported."
        self.assert_model_exists("action_worker/4")

    def test_import_warning_state_action_worker6(self) -> None:
        response = self.request("account.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.DONE
        assert entry["messages"] == ["test"]
        self.assert_model_not_exists("action_worker/6")

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
        self.assert_model_exists("user/35", {"username": "test_saml_id2", "saml_id": "test_saml_id", "default_password": "", "can_change_own_password": False, "default_vote_weight": "1.000000"})
        self.assert_model_exists("user/36", {"username": "test_saml_id1", "saml_id": None, "can_change_own_password": True, "default_vote_weight": "1.000000"})
        self.assert_model_exists("user/37", {"username": "test_saml_id21", "saml_id": None, "can_change_own_password": True, "default_vote_weight": "1.000000"})
        self.assert_model_not_exists("action_worker/1")

    def test_upload_import_with_generated_usernames_error_username(self) -> None:
        self.json_upload_saml_id_new()
        self.set_models({
            "user/33": {"username": "test_saml_id21"}
        })
        response = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][2]["state"] == ImportState.ERROR
        assert response.json["results"][0][0]["rows"][2]["messages"] == ["Error: want to create a new user, but username already exists."]
        assert response.json["results"][0][0]["rows"][2]["data"]["username"] == 'test_saml_id21'
        self.assert_model_not_exists("user/35")
        self.assert_model_not_exists("user/36")
        self.assert_model_not_exists("user/37")
        self.assert_model_exists("action_worker/1")

    def test_json_upload_set_saml_id_in_existing_account(self) -> None:
        self.json_upload_set_saml_id_in_existing_account()
        response_import = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        self.assert_model_exists("user/2", {"username": "test", "saml_id": "test_saml_id", "default_password": "", "can_change_own_password": False, "password": "", "default_vote_weight": "2.300000"})
        self.assert_model_not_exists("action_worker/1")

    def test_json_upload_update_saml_id_in_existing_account(self) -> None:
        self.json_upload_update_saml_id_in_existing_account()
        response_import = self.request("account.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        self.assert_model_exists("user/2", {"username": "test", "saml_id": "new_one", "default_vote_weight": "2.300000"})
        self.assert_model_not_exists("action_worker/1")
