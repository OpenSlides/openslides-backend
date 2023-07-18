from typing import Any, Dict

from openslides_backend.action.mixins.import_mixins import ImportState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class UserJsonImport(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "action_worker/2": {
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
            }
        )

    def test_import_username_and_create(self) -> None:
        response = self.request("user.import", {"id": 2, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"username": "test", "first_name": "Testy"},
        )
        self.assert_model_not_exists("action_worker/2")

    def test_import_abort(self) -> None:
        response = self.request("user.import", {"id": 2, "import": False})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("action_worker/2")
        self.assert_model_not_exists("user/2")

    def test_import_wrong_action_worker(self) -> None:
        response = self.request("user.import", {"id": 5, "import": True})
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
        response = self.request("user.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/2")
        self.assert_model_exists("user/1", {"first_name": "Testy"})

    def test_import_names_and_email_and_create(self) -> None:
        response = self.request("user.import", {"id": 3, "import": True})
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
        self, number: int, state: ImportState, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            f"action_worker/{number}": {
                "result": {
                    "import": "account",
                    "rows": [
                        {
                            "state": state,
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
                6,
                ImportState.NEW,
                {"saml_id": {"value": "testsaml", "info": ImportState.NEW}},
            )
        )
        response = self.request("user.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
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
        response = self.request("user.import", {"id": 6, "import": True})
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
        response = self.request("user.import", {"id": 6, "import": True})
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
        response = self.request("user.import", {"id": 6, "import": True})
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
        response = self.request("user.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: Want to create user, but missing username in import data."
        ]

        response = self.request("user.import", {"id": 7, "import": True})
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
        response = self.request("user.import", {"id": 6, "import": True})
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
        response = self.request("user.import", {"id": 6, "import": True})
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
        response = self.request("user.import", {"id": 6, "import": True})
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
        response = self.request("user.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: want to update, but found search data doesn't match."
        ]

    def test_import_error_state(self) -> None:
        response = self.request("user.import", {"id": 4, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == ["test", "Error in import."]
        self.assert_model_exists("action_worker/4")

    def test_import_no_permission(self) -> None:
        self.base_permission_test({}, "user.import", {"id": 2, "import": True})

    def test_import_permission(self) -> None:
        self.base_permission_test(
            {},
            "user.import",
            {"id": 2, "import": True},
            OrganizationManagementLevel.CAN_MANAGE_USERS,
        )
