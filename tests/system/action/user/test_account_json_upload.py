from time import time

from openslides_backend.action.mixins.import_mixins import ImportState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class AccountJsonUpload(BaseActionTestCase):
    def test_json_upload_simple(self) -> None:
        start_time = int(time())
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "test",
                        "default_password": "secret",
                        "is_active": "1",
                        "is_physical_person": "F",
                        "wrong": 15,
                    }
                ],
            },
        )
        end_time = int(time())
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "username": {"value": "test", "info": ImportState.DONE},
                "default_password": {"value": "secret", "info": ImportState.DONE},
                "is_active": True,
                "is_physical_person": False,
            },
        }
        worker = self.assert_model_exists("action_worker/1")
        assert worker["result"]["import"] == "account"
        assert start_time <= worker["created"] <= end_time
        assert start_time <= worker["timestamp"] <= end_time

    def test_json_upload_empty_data(self) -> None:
        response = self.request(
            "account.json_upload",
            {"data": []},
        )
        self.assert_status_code(response, 400)
        assert "data.data must contain at least 1 items" in response.json["message"]

    def test_json_upload_parse_boolean_error(self) -> None:
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "test",
                        "default_password": "secret",
                        "is_physical_person": "X50",
                    }
                ],
            },
        )
        self.assert_status_code(response, 400)
        assert "Could not parse X50 expect boolean" in response.json["message"]

    def test_json_upload_results(self) -> None:
        response = self.request(
            "account.json_upload",
            {"data": [{"username": "test", "default_password": "secret"}]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "action_worker/1",
            {
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
                                "default_password": {
                                    "value": "secret",
                                    "info": ImportState.DONE,
                                },
                            },
                        }
                    ],
                }
            },
        )
        result = response.json["results"][0][0]
        assert result == {
            "id": 1,
            "headers": [
                {"property": "title", "type": "string"},
                {"property": "first_name", "type": "string"},
                {"property": "last_name", "type": "string"},
                {"property": "is_active", "type": "boolean"},
                {"property": "is_physical_person", "type": "boolean"},
                {"property": "default_password", "type": "string", "is_object": True},
                {"property": "email", "type": "string"},
                {"property": "username", "type": "string", "is_object": True},
                {"property": "gender", "type": "string"},
                {"property": "pronoun", "type": "string"},
                {"property": "saml_id", "type": "string", "is_object": True},
            ],
            "rows": [
                {
                    "state": ImportState.NEW,
                    "messages": [],
                    "data": {
                        "username": {"value": "test", "info": ImportState.DONE},
                        "default_password": {
                            "value": "secret",
                            "info": ImportState.DONE,
                        },
                    },
                }
            ],
            "statistics": [
                {"name": "total", "value": 1},
                {"name": "created", "value": 1},
                {"name": "updated", "value": 0},
                {"name": "error", "value": 0},
                {"name": "warning", "value": 0},
            ],
            "state": ImportState.DONE,
        }

    def test_json_upload_duplicate_in_db(self) -> None:
        self.set_models(
            {
                "user/3": {
                    "username": "test",
                    "saml_id": "12345",
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "email": "max@mustermann.org",
                },
            },
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {"username": "test"},
                    {"saml_id": "12345"},
                    {
                        "first_name": "Max",
                        "last_name": "Mustermann",
                        "email": "max@mustermann.org",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["rows"] == [
            {
                "state": ImportState.ERROR,
                "messages": [
                    "The account with id 3 was found multiple times by different search criteria."
                ],
                "data": {
                    "username": {"value": "test", "info": "done", "id": 3},
                    "id": 3,
                },
            },
            {
                "state": ImportState.ERROR,
                "messages": [
                    "The account with id 3 was found multiple times by different search criteria."
                ],
                "data": {
                    "saml_id": {"value": "12345", "info": "done"},
                    "id": 3,
                    "username": {"value": "test", "info": "done", "id": 3},
                },
            },
            {
                "state": ImportState.ERROR,
                "messages": [
                    "The account with id 3 was found multiple times by different search criteria."
                ],
                "data": {
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "email": "max@mustermann.org",
                    "id": 3,
                    "username": {"value": "test", "info": "done", "id": 3},
                },
            },
        ]

    def test_json_upload_multiple_duplicates(self) -> None:
        self.set_models(
            {
                "user/3": {
                    "username": "test",
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "email": "max@mustermann.org",
                },
                "user/4": {
                    "username": "test2",
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "email": "max@mustermann.org",
                },
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "first_name": "Max",
                        "last_name": "Mustermann",
                        "email": "max@mustermann.org",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["rows"] == [
            {
                "state": ImportState.ERROR,
                "messages": ["Found more users with name and email"],
                "data": {
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "email": "max@mustermann.org",
                },
            }
        ]

    def test_json_upload_username_duplicate_in_data(self) -> None:
        self.maxDiff = None
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {"username": "test", "default_password": "secret"},
                    {"username": "bla", "default_password": "secret"},
                    {"username": "test", "default_password": "secret"},
                ],
            },
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["rows"][0]["messages"] == [
            "Found more users with the same username"
        ]
        assert result["rows"][0]["state"] == ImportState.ERROR
        assert result["rows"][2]["messages"] == [
            "Found more users with the same username"
        ]
        assert result["rows"][2]["state"] == ImportState.ERROR
        self.assert_model_exists(
            "action_worker/1",
            {
                "id": 1,
                "state": ImportState.ERROR,
                "result": {
                    "import": "account",
                    "rows": [
                        {
                            "state": ImportState.ERROR,
                            "messages": ["Found more users with the same username"],
                            "data": {
                                "username": {
                                    "value": "test",
                                    "info": ImportState.ERROR,
                                },
                                "default_password": {
                                    "value": "secret",
                                    "info": ImportState.DONE,
                                },
                            },
                        },
                        {
                            "state": ImportState.NEW,
                            "messages": [],
                            "data": {
                                "username": {"value": "bla", "info": ImportState.DONE},
                                "default_password": {
                                    "value": "secret",
                                    "info": ImportState.DONE,
                                },
                            },
                        },
                        {
                            "state": ImportState.ERROR,
                            "messages": ["Found more users with the same username"],
                            "data": {
                                "username": {
                                    "value": "test",
                                    "info": ImportState.ERROR,
                                },
                                "default_password": {
                                    "value": "secret",
                                    "info": ImportState.DONE,
                                },
                            },
                        },
                    ],
                },
            },
        )

    def test_json_upload_names_and_email_generate_username(self) -> None:
        self.set_models(
            {
                "user/34": {
                    "username": "MaxMustermann",
                    "first_name": "Testy",
                    "last_name": "Tester",
                }
            }
        )

        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "first_name": "Max",
                        "last_name": "Mustermann",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.NEW
        assert entry["data"]["first_name"] == "Max"
        assert entry["data"]["last_name"] == "Mustermann"
        assert entry["data"]["username"] == {
            "value": "MaxMustermann1",
            "info": ImportState.GENERATED,
        }
        assert entry["data"]["default_password"]["info"] == ImportState.GENERATED

    def test_json_upload_names_and_email_set_username(self) -> None:
        self.set_models(
            {
                "user/34": {
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "email": "test@ntvtn.de",
                    "username": "test",
                }
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "first_name": "Max",
                        "last_name": "Mustermann",
                        "email": "test@ntvtn.de",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["data"]["first_name"] == "Max"
        assert entry["data"]["last_name"] == "Mustermann"
        assert entry["data"]["id"] == 34
        assert entry["data"]["username"]["value"] == "test"

    def test_json_upload_generate_default_password(self) -> None:
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "test",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        worker = self.assert_model_exists("action_worker/1")
        assert worker["result"]["import"] == "account"
        assert worker["result"]["rows"][0]["data"].get("default_password")
        assert (
            worker["result"]["rows"][0]["data"]["default_password"]["info"]
            == ImportState.GENERATED
        )

    def test_json_upload_saml_id(self) -> None:
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "saml_id": "test_saml_id",
                        "password": "test2",
                        "default_password": "test3",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        worker = self.assert_model_exists("action_worker/1")
        assert worker["result"]["import"] == "account"
        assert worker["result"]["rows"][0]["messages"] == [
            "Removed password or default_password from entry."
        ]
        data = worker["result"]["rows"][0]["data"]
        assert data == {
            "saml_id": {"info": "new", "value": "test_saml_id"},
            "username": {"info": "generated", "value": "test_saml_id"},
            "can_change_own_password": False,
        }

    def test_json_upload_duplicated_one_saml_id(self) -> None:
        self.set_models(
            {
                "user/3": {
                    "username": "test",
                    "saml_id": "12345",
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "email": "max@mustermann.org",
                },
            },
        )

        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "test2",
                        "saml_id": "12345",
                        "first_name": "John",
                        "default_password": "test3",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["rows"] == [
            {
                "state": ImportState.ERROR,
                "messages": [
                    "saml_id 12345 must be unique.",
                    "Removed password or default_password from entry.",
                ],
                "data": {
                    "username": {"value": "test2", "info": ImportState.DONE},
                    "saml_id": {"value": "12345", "info": "error"},
                    "first_name": "John",
                    "can_change_own_password": False,
                },
            }
        ]
        assert result["statistics"] == [
            {"name": "total", "value": 1},
            {"name": "created", "value": 0},
            {"name": "updated", "value": 0},
            {"name": "error", "value": 1},
            {"name": "warning", "value": 0},
        ]
        assert result["state"] == ImportState.ERROR

    def test_json_upload_duplicated_two_new_saml_ids(self) -> None:
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "test1",
                        "saml_id": "12345",
                    },
                    {
                        "username": "test2",
                        "saml_id": "12345",
                    },
                ],
            },
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["rows"] == [
            {
                "state": ImportState.ERROR,
                "messages": [
                    "saml_id 12345 must be unique.",
                    "Removed password or default_password from entry.",
                ],
                "data": {
                    "username": {"value": "test1", "info": ImportState.DONE},
                    "saml_id": {"value": "12345", "info": ImportState.ERROR},
                    "can_change_own_password": False,
                },
            },
            {
                "state": ImportState.ERROR,
                "messages": [
                    "saml_id 12345 must be unique.",
                    "Removed password or default_password from entry.",
                ],
                "data": {
                    "username": {"value": "test2", "info": ImportState.DONE},
                    "saml_id": {"value": "12345", "info": ImportState.ERROR},
                    "can_change_own_password": False,
                },
            },
        ]
        assert result["statistics"] == [
            {"name": "total", "value": 2},
            {"name": "created", "value": 0},
            {"name": "updated", "value": 0},
            {"name": "error", "value": 2},
            {"name": "warning", "value": 0},
        ]
        assert result["state"] == ImportState.ERROR

    def test_json_upload_duplicated_two_found_saml_ids(self) -> None:
        self.set_models(
            {
                "user/3": {
                    "username": "test1",
                    "saml_id": "1",
                },
                "user/4": {
                    "username": "test2",
                    "saml_id": "2",
                },
            },
        )

        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "test1",
                        "saml_id": "12345",
                    },
                    {
                        "username": "test2",
                        "saml_id": "12345",
                    },
                ],
            },
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["rows"] == [
            {
                "state": ImportState.ERROR,
                "messages": ["saml_id 12345 must be unique."],
                "data": {
                    "username": {"value": "test1", "info": "done", "id": 3},
                    "saml_id": {"value": "12345", "info": "error"},
                    "id": 3,
                },
            },
            {
                "state": ImportState.ERROR,
                "messages": ["saml_id 12345 must be unique."],
                "data": {
                    "username": {"value": "test2", "info": "done", "id": 4},
                    "saml_id": {"value": "12345", "info": "error"},
                    "id": 4,
                },
            },
        ]
        assert result["statistics"] == [
            {"name": "total", "value": 2},
            {"name": "created", "value": 0},
            {"name": "updated", "value": 0},
            {"name": "error", "value": 2},
            {"name": "warning", "value": 0},
        ]
        assert result["state"] == ImportState.ERROR

    def test_json_upload_no_permission(self) -> None:
        self.base_permission_test(
            {}, "account.json_upload", {"data": [{"username": "test"}]}
        )

    def test_json_upload_permission(self) -> None:
        self.base_permission_test(
            {},
            "account.json_upload",
            {"data": [{"username": "test"}]},
            OrganizationManagementLevel.CAN_MANAGE_USERS,
        )
