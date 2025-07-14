from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from openslides_backend.action.mixins.import_mixins import ImportState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.patterns import fqid_from_collection_and_id, id_from_fqid
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class AccountJsonUpload(BaseActionTestCase):
    def test_json_upload_simple(self) -> None:
        start_time = datetime.now(ZoneInfo(key="Etc/UTC"))
        self.set_models(
            {
                "organization/1": {"gender_ids": [1, 2, 3, 4]},
                "gender/1": {"name": "male"},
                "gender/2": {"name": "female"},
                "gender/3": {"name": "diverse"},
                "gender/4": {"name": "non-binary"},
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "test",
                        "default_password": "secret",
                        "is_active": "1",
                        "is_physical_person": "F",
                        "default_vote_weight": "1.12",
                        "wrong": 15,
                        "gender": "female",
                    }
                ],
            },
        )
        end_time = datetime.now(ZoneInfo(key="Etc/UTC"))
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "username": {"value": "test", "info": ImportState.DONE},
                "default_password": {"value": "secret", "info": ImportState.DONE},
                "is_active": {"value": True, "info": ImportState.DONE},
                "is_physical_person": {"value": False, "info": ImportState.DONE},
                "default_vote_weight": {"value": "1.120000", "info": ImportState.DONE},
                "gender": {"id": 2, "value": "female", "info": ImportState.DONE},
            },
        }
        import_preview_id = response.json["results"][0][0].get("id")
        import_preview_fqid = fqid_from_collection_and_id(
            "import_preview", import_preview_id
        )
        import_preview = self.assert_model_exists(
            import_preview_fqid, {"name": "account"}
        )
        assert start_time <= import_preview["created"] <= end_time

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

    def test_json_upload_without_names_error(self) -> None:
        response = self.request(
            "account.json_upload",
            {
                "data": [{}],
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.ERROR,
            "messages": [
                "Cannot generate username. Missing one of first_name, last_name."
            ],
            "data": {
                "username": {"value": "", "info": ImportState.GENERATED},
            },
        }

    def test_json_upload_results(self) -> None:
        response = self.request(
            "account.json_upload",
            {"data": [{"username": "test", "default_password": "secret"}]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "import_preview/1",
            {
                "name": "account",
                "state": ImportState.DONE,
                "result": {
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
                },
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
                {"property": "email", "type": "string", "is_object": True},
                {"property": "username", "type": "string", "is_object": True},
                {"property": "gender", "type": "string", "is_object": True},
                {"property": "pronoun", "type": "string"},
                {"property": "saml_id", "type": "string", "is_object": True},
                {"property": "member_number", "type": "string", "is_object": True},
                {"property": "home_committee", "type": "string", "is_object": True},
                {"property": "guest", "type": "boolean", "is_object": True},
                {
                    "property": "default_vote_weight",
                    "type": "decimal",
                    "is_object": True,
                },
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
                    "Found more users with the same username",
                ],
                "data": {
                    "username": {"value": "test", "info": ImportState.ERROR},
                },
            },
            {
                "state": ImportState.ERROR,
                "messages": [
                    "The account with id 3 was found multiple times by different search criteria.",
                ],
                "data": {
                    "saml_id": {"value": "12345", "info": ImportState.DONE},
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
                    "first_name": {"value": "Max", "info": ImportState.DONE},
                    "last_name": {"value": "Mustermann", "info": ImportState.DONE},
                    "email": {"value": "max@mustermann.org", "info": ImportState.DONE},
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
                    "id": 4,
                    "first_name": {"value": "Max", "info": ImportState.DONE},
                    "last_name": {"value": "Mustermann", "info": ImportState.DONE},
                    "email": {"value": "max@mustermann.org", "info": ImportState.DONE},
                    "username": {"id": 4, "value": "test2", "info": ImportState.DONE},
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
            "import_preview/1",
            {
                "id": 1,
                "name": "account",
                "state": ImportState.ERROR,
                "result": {
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

    def test_json_upload_duplicated_one_saml_id(self) -> None:
        self.set_models(
            {
                "user/3": {
                    "username": "test",
                    "saml_id": "12345",
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "email": "max@mustermann.org",
                    "default_password": "test1",
                    "password": "secret",
                    "can_change_own_password": True,
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
                        "default_password": "test2",
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
                    "Because this account is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
                ],
                "data": {
                    "username": {"value": "test2", "info": ImportState.DONE},
                    "saml_id": {"value": "12345", "info": ImportState.ERROR},
                    "first_name": {"value": "John", "info": ImportState.DONE},
                    "default_password": {"value": "", "info": ImportState.WARNING},
                },
            }
        ]
        assert result["statistics"] == [
            {"name": "total", "value": 1},
            {"name": "created", "value": 0},
            {"name": "updated", "value": 0},
            {"name": "error", "value": 1},
            {"name": "warning", "value": 1},
        ]
        assert result["state"] == ImportState.ERROR

    def test_json_upload_create_broken_username_error(self) -> None:
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "has space",
                        "default_password": "ilikespace",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["rows"] == [
            {
                "state": ImportState.ERROR,
                "messages": ["Error: Empty spaces not allowed in new usernames"],
                "data": {
                    "username": {"value": "has space", "info": ImportState.ERROR},
                    "default_password": {
                        "value": "ilikespace",
                        "info": ImportState.DONE,
                    },
                },
            }
        ]

    def test_json_upload_duplicated_two_new_saml_ids1(self) -> None:
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
                        "default_password": "def_password",
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
                    "username": {"value": "test1", "info": ImportState.DONE},
                    "saml_id": {"value": "12345", "info": ImportState.ERROR},
                },
            },
            {
                "state": ImportState.ERROR,
                "messages": [
                    "saml_id 12345 must be unique.",
                    "Because this account is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
                ],
                "data": {
                    "username": {"value": "test2", "info": ImportState.DONE},
                    "saml_id": {"value": "12345", "info": ImportState.ERROR},
                    "default_password": {"info": ImportState.WARNING, "value": ""},
                },
            },
        ]
        assert result["statistics"] == [
            {"name": "total", "value": 2},
            {"name": "created", "value": 0},
            {"name": "updated", "value": 0},
            {"name": "error", "value": 2},
            {"name": "warning", "value": 1},
        ]
        assert result["state"] == ImportState.ERROR

    def test_json_upload_duplicated_two_new_saml_ids2(self) -> None:
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "saml_id": "12345",
                    },
                    {
                        "saml_id": "12345",
                        "default_password": "def_password",
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
                    "username": {"value": "12345", "info": ImportState.GENERATED},
                    "saml_id": {"value": "12345", "info": ImportState.ERROR},
                },
            },
            {
                "state": ImportState.ERROR,
                "messages": [
                    "saml_id 12345 must be unique.",
                    "Because this account is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
                ],
                "data": {
                    "username": {"value": "123451", "info": ImportState.GENERATED},
                    "saml_id": {"value": "12345", "info": ImportState.ERROR},
                    "default_password": {"info": ImportState.WARNING, "value": ""},
                },
            },
        ]
        assert result["statistics"] == [
            {"name": "total", "value": 2},
            {"name": "created", "value": 0},
            {"name": "updated", "value": 0},
            {"name": "error", "value": 2},
            {"name": "warning", "value": 1},
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
                    "username": {"value": "test1", "info": ImportState.DONE, "id": 3},
                    "saml_id": {"value": "12345", "info": ImportState.ERROR},
                    "id": 3,
                },
            },
            {
                "state": ImportState.ERROR,
                "messages": ["saml_id 12345 must be unique."],
                "data": {
                    "username": {"value": "test2", "info": ImportState.DONE, "id": 4},
                    "saml_id": {"value": "12345", "info": ImportState.ERROR},
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

    def test_json_upload_duplicate_existing_name_email(self) -> None:
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
                        "first_name": "Max",
                        "last_name": "Mustermann",
                        "email": "max@mustermann.org",
                        "default_vote_weight": "1.0",
                    },
                    {
                        "first_name": "Max",
                        "last_name": "Mustermann",
                        "email": "max@mustermann.org",
                        "default_vote_weight": "2.0",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.ERROR
        assert result["rows"][0]["messages"] == ["Found more users with name and email"]
        assert result["rows"][0]["state"] == ImportState.ERROR
        assert result["rows"][0]["data"] == {
            "id": 3,
            "first_name": {"value": "Max", "info": ImportState.DONE},
            "last_name": {"value": "Mustermann", "info": ImportState.DONE},
            "email": {"value": "max@mustermann.org", "info": ImportState.DONE},
            "default_vote_weight": {"value": "1.000000", "info": ImportState.DONE},
            "username": {"value": "test", "info": ImportState.DONE, "id": 3},
        }
        assert result["rows"][1]["messages"] == ["Found more users with name and email"]
        assert result["rows"][1]["state"] == ImportState.ERROR
        assert result["rows"][1]["data"] == {
            "id": 3,
            "first_name": {"value": "Max", "info": ImportState.DONE},
            "last_name": {"value": "Mustermann", "info": ImportState.DONE},
            "email": {"value": "max@mustermann.org", "info": ImportState.DONE},
            "default_vote_weight": {"value": "2.000000", "info": ImportState.DONE},
            "username": {"value": "test", "info": ImportState.DONE, "id": 3},
        }

    def test_json_upload_invalid_vote_weight(self) -> None:
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "first_name": "Max",
                        "last_name": "Mustermann",
                        "email": "max@mustermann.org",
                        "default_vote_weight": "0",
                        "default_password": "halloIchBinMax",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.ERROR
        assert result["rows"][0]["messages"] == [
            "default_vote_weight must be bigger than or equal to 0.000001."
        ]
        assert result["rows"][0]["state"] == ImportState.ERROR
        assert result["rows"][0]["data"] == {
            "first_name": {"value": "Max", "info": ImportState.DONE},
            "last_name": {"value": "Mustermann", "info": ImportState.DONE},
            "email": {"value": "max@mustermann.org", "info": ImportState.DONE},
            "default_vote_weight": {"value": "0.000000", "info": ImportState.ERROR},
            "username": {"value": "MaxMustermann", "info": ImportState.GENERATED},
            "default_password": {"value": "halloIchBinMax", "info": ImportState.DONE},
        }

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

    def test_json_upload_wrong_email(self) -> None:
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {"username": "test1", "email": "veryveryverybad"},
                    {"username": "test2", "email": "slightly@bad"},
                    {"username": "test3", "email": "somewhat@@worse"},
                    {"username": "test4", "email": "this.is@wrong,too"},
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["name"] == "account"
        assert import_preview["state"] == ImportState.ERROR
        rows = import_preview["result"]["rows"]
        row = rows[0]
        assert row["data"]["email"] == {
            "value": "veryveryverybad",
            "info": ImportState.ERROR,
        }
        assert (
            "Error: 'veryveryverybad' is not a valid email address." in row["messages"]
        )
        row = rows[1]
        assert row["data"]["email"] == {
            "value": "slightly@bad",
            "info": ImportState.ERROR,
        }
        assert "Error: 'slightly@bad' is not a valid email address." in row["messages"]
        row = rows[2]
        assert row["data"]["email"] == {
            "value": "somewhat@@worse",
            "info": ImportState.ERROR,
        }
        assert (
            "Error: 'somewhat@@worse' is not a valid email address." in row["messages"]
        )
        row = rows[3]
        assert row["data"]["email"] == {
            "value": "this.is@wrong,too",
            "info": ImportState.ERROR,
        }
        assert (
            "Error: 'this.is@wrong,too' is not a valid email address."
            in row["messages"]
        )

    def test_json_upload_update_member_number_in_existing_account_error(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "test",
                    "default_vote_weight": "2.300000",
                    "member_number": "old_one",
                }
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "test",
                        "member_number": "new_one",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Member numbers can't be updated via import"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "member_number": {"info": ImportState.ERROR, "value": "new_one"},
            "username": {"info": "done", "value": "test", "id": 2},
        }

    def test_json_upload_update_duplicate_member_numbers(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "test1",
                    "default_vote_weight": "2.300000",
                },
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "test1",
                        "member_number": "new_one",
                    },
                    {
                        "username": "test2",
                        "member_number": "new_one",
                    },
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Found more users with the same member number"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "member_number": {"info": ImportState.ERROR, "value": "new_one"},
            "username": {"info": "done", "value": "test1", "id": 2},
        }
        assert import_preview["result"]["rows"][1]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][1]["messages"] == [
            "Error: Found more users with the same member number"
        ]
        data = import_preview["result"]["rows"][1]["data"]
        assert data == {
            "member_number": {"info": ImportState.ERROR, "value": "new_one"},
            "username": {"info": "done", "value": "test2"},
        }

    def test_json_upload_set_other_persons_member_number_in_existing_account(
        self,
    ) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "test",
                    "default_vote_weight": "2.300000",
                },
                "user/3": {
                    "username": "test2",
                    "member_number": "new_one",
                    "default_vote_weight": "2.300000",
                },
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "test",
                        "member_number": "new_one",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Member number doesn't match detected user"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "member_number": {"info": ImportState.ERROR, "value": "new_one"},
            "username": {"info": "done", "value": "test", "id": 2},
        }

    def test_json_upload_set_other_persons_member_number_in_existing_account_2(
        self,
    ) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "test",
                    "default_vote_weight": "2.300000",
                    "saml_id": "tessst",
                },
                "user/3": {
                    "username": "test2",
                    "member_number": "new_one",
                    "default_vote_weight": "2.300000",
                },
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "saml_id": "tessst",
                        "member_number": "new_one",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Member number doesn't match detected user"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "member_number": {"info": ImportState.ERROR, "value": "new_one"},
            "username": {"info": "done", "value": "test", "id": 2},
            "saml_id": {"info": "done", "value": "tessst"},
        }

    def test_json_upload_set_other_persons_member_number_in_existing_account_3(
        self,
    ) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "test",
                    "default_vote_weight": "2.300000",
                    "first_name": "Fritz",
                    "last_name": "Chen",
                    "email": "fritz.chen@scho.ol",
                },
                "user/3": {
                    "username": "test2",
                    "member_number": "new_one",
                    "default_vote_weight": "2.300000",
                },
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "member_number": "new_one",
                        "first_name": "Fritz",
                        "last_name": "Chen",
                        "email": "fritz.chen@scho.ol",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Member number doesn't match detected user"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "member_number": {"info": ImportState.ERROR, "value": "new_one"},
            "username": {"info": "done", "value": "test", "id": 2},
            "first_name": {"info": ImportState.DONE, "value": "Fritz"},
            "last_name": {"info": ImportState.DONE, "value": "Chen"},
            "email": {"info": "done", "value": "fritz.chen@scho.ol"},
        }

    def test_json_upload_new_account_with_only_member_number_and_incompatible_username_generation_error(
        self,
    ) -> None:
        self.create_user("M3MNUM")
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "member_number": "M3MNUM",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Cannot generate username. Missing one of first_name, last_name."
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data["username"] == {"info": "generated", "value": ""}
        assert data["member_number"] == {"info": "done", "value": "M3MNUM"}

    def test_json_upload_2_new_accounts_with_only_member_number_error(
        self,
    ) -> None:
        self.create_user("M3MNUM")
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "member_number": "M3MNUM",
                    },
                    {
                        "member_number": "M4MNUM",
                    },
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "account"
        for i in range(0, 2):
            assert import_preview["result"]["rows"][i]["state"] == ImportState.ERROR
            assert import_preview["result"]["rows"][i]["messages"] == [
                "Cannot generate username. Missing one of first_name, last_name."
            ]
            data = import_preview["result"]["rows"][i]["data"]
            assert data["username"] == {"info": "generated", "value": ""}
        assert import_preview["result"]["rows"][0]["data"]["member_number"] == {
            "info": "done",
            "value": "M3MNUM",
        }
        assert import_preview["result"]["rows"][1]["data"]["member_number"] == {
            "info": "done",
            "value": "M4MNUM",
        }

    def test_json_upload_dont_recognize_empty_name_and_email(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "organization/1": {
                    "saml_enabled": False,
                },
                "gender/4": {"name": "non-binary faun"},
                "user/3": {
                    "email": "",
                    "default_password": "password",
                    "password": self.auth.hash("password"),
                    "username": "a",
                    "last_name": "",
                    "first_name": "",
                    "organization_id": 1,
                },
                "user/4": {
                    "email": "",
                    "default_password": "password",
                    "password": self.auth.hash("password"),
                    "username": "b",
                    "last_name": "",
                    "first_name": "",
                    "organization_id": 1,
                },
                "user/5": {
                    "email": "balu@ntvtn.de",
                    "title": "title",
                    "gender_id": 4,
                    "pronoun": "pronoun",
                    "password": "$argon2id$v=19$m=65536,t=3,p=4$iQbqhQ2/XYiFnO6vP6rtGQ$Bv3QuH4l9UQACws9hiuCCUBQepVRnCTqmOn5TkXfnQ8",
                    "username": "balubear",
                    "is_active": True,
                    "last_name": "bear",
                    "first_name": "balu",
                    "member_number": "mem_nr",
                    "organization_id": 1,
                    "default_password": "aU3seRYj8N",
                    "is_physical_person": True,
                    "default_vote_weight": "1.000000",
                    "can_change_own_password": True,
                    "committee_management_ids": [],
                },
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "member_number": "mem_nr",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE

    def test_json_upload_new_account_with_only_member_number(self) -> None:
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "member_number": "M3MNUM",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Cannot generate username. Missing one of first_name, last_name."
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data["username"] == {"info": "generated", "value": ""}
        assert data["member_number"] == {"info": "done", "value": "M3MNUM"}

    def test_json_upload_set_home_committee_not_found(self) -> None:
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "first_name": "Bob",
                        "last_name": "will fail",
                        "username": "BobWillFail",
                        "home_committee": "Does not exist",
                        "default_password": "ouch",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Home committee not found."
        ]
        assert import_preview["result"]["rows"][0]["data"] == {
            "first_name": {"value": "Bob", "info": ImportState.DONE},
            "last_name": {"value": "will fail", "info": ImportState.DONE},
            "username": {"value": "BobWillFail", "info": ImportState.DONE},
            "home_committee": {"value": "Does not exist", "info": ImportState.ERROR},
            "default_password": {"value": "ouch", "info": ImportState.DONE},
            "guest": {"value": False, "info": ImportState.GENERATED},
        }

    def test_json_upload_set_home_committee_multiple_found(self) -> None:
        self.create_committee(1, name="There are two")
        self.create_committee(2, name="There are two")
        self.create_user("BobWillFail")
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "first_name": "Bob",
                        "last_name": "will fail",
                        "username": "BobWillFail",
                        "home_committee": "There are two",
                        "default_password": "ouch",
                        "guest": "0",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Found multiple committees with the same name as the home committee."
        ]
        assert import_preview["result"]["rows"][0]["data"] == {
            "id": 2,
            "first_name": {"value": "Bob", "info": ImportState.DONE},
            "last_name": {"value": "will fail", "info": ImportState.DONE},
            "username": {"id": 2, "value": "BobWillFail", "info": ImportState.DONE},
            "home_committee": {"value": "There are two", "info": ImportState.ERROR},
            "default_password": {"value": "ouch", "info": ImportState.DONE},
            "guest": {"value": False, "info": ImportState.DONE},
        }

    def test_json_set_home_committee_and_set_guest_to_true(self) -> None:
        self.create_committee(1, name="Home")
        self.create_committee(2, name="Old home")
        self.create_user("BobWillFail", home_committee_id=2)
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "first_name": "Bob",
                        "last_name": "will fail",
                        "username": "BobWillFail",
                        "home_committee": "Home",
                        "default_password": "ouch",
                        "guest": "1",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Cannot set guest to true while setting home committee."
        ]
        assert import_preview["result"]["rows"][0]["data"] == {
            "id": 2,
            "first_name": {"value": "Bob", "info": ImportState.DONE},
            "last_name": {"value": "will fail", "info": ImportState.DONE},
            "username": {"id": 2, "value": "BobWillFail", "info": ImportState.DONE},
            "home_committee": {"id": 1, "value": "Home", "info": ImportState.DONE},
            "default_password": {"value": "ouch", "info": ImportState.DONE},
            "guest": {"value": True, "info": ImportState.ERROR},
        }

    def test_json_upload_set_home_committee_without_permission_and_set_guest_to_true(
        self,
    ) -> None:
        self.create_committee(1, name="Home")
        self.create_committee(2, name="Old home")
        self.create_user("Alice", home_committee_id=2)
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "Alice",
                        "home_committee": "Home",
                        "guest": "1",
                        "first_name": "alice",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Cannot set guest to true while setting home committee.",
            "Account is updated, but changes to the following field(s) are not possible: home_committee, guest",
        ]
        assert import_preview["result"]["rows"][0]["data"] == {
            "id": 2,
            "username": {"id": 2, "value": "Alice", "info": ImportState.DONE},
            "home_committee": {"id": 1, "value": "Home", "info": ImportState.REMOVE},
            "guest": {"value": True, "info": ImportState.ERROR},
            "first_name": {"value": "alice", "info": ImportState.DONE},
        }

    def test_json_upload_perm_superadmin_self_set_inactive_error(self) -> None:
        """SUPERADMIN may not set himself inactive."""
        response = self.request(
            "account.json_upload",
            {
                "data": [{"username": "admin", "is_active": "False"}],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["data"]["is_active"] == {
            "value": False,
            "info": ImportState.ERROR,
        }
        assert (
            "A superadmin is not allowed to set himself inactive."
            in import_preview["result"]["rows"][0]["messages"]
        )


class AccountJsonUploadForUseInImport(BaseActionTestCase):
    def json_upload_saml_id_new(self) -> None:
        self.set_models(
            {
                "user/34": {
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "email": "test@ntvtn.de",
                    "username": "test_saml_id",
                }
            }
        )

        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "saml_id": "test_saml_id",
                        "default_password": "test2",
                    },
                    {
                        "username": "test_saml_id1",
                    },
                    {
                        "first_name": "test_sa",
                        "last_name": "ml_id2",
                    },
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Because this account is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides."
        ]
        assert import_preview["result"]["rows"][0]["state"] == ImportState.NEW
        data0 = import_preview["result"]["rows"][0]["data"]
        assert data0 == {
            "saml_id": {"info": "new", "value": "test_saml_id"},
            "username": {"info": "generated", "value": "test_saml_id2"},
            "default_password": {"info": "warning", "value": ""},
        }
        assert import_preview["result"]["rows"][1]["data"]["username"] == {
            "info": "done",
            "value": "test_saml_id1",
        }
        assert import_preview["result"]["rows"][2]["data"]["username"] == {
            "info": "generated",
            "value": "test_saml_id21",
        }
        assert import_preview["result"]["rows"][2]["data"]["last_name"] == {
            "info": "done",
            "value": "ml_id2",
        }
        assert import_preview["result"]["rows"][2]["data"]["first_name"] == {
            "info": "done",
            "value": "test_sa",
        }

    def json_upload_set_saml_id_in_existing_account(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "test",
                    "password": "secret",
                    "default_password": "secret",
                    "can_change_own_password": True,
                    "default_vote_weight": "2.300000",
                }
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "test",
                        "saml_id": "test_saml_id",
                        "default_password": "secret2",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.WARNING
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Because this account is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides."
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "saml_id": {"info": "new", "value": "test_saml_id"},
            "username": {"info": "done", "value": "test", "id": 2},
            "default_password": {"info": "warning", "value": ""},
        }

    def json_upload_update_saml_id_in_existing_account(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "test",
                    "default_vote_weight": "2.300000",
                    "saml_id": "old_one",
                }
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "test",
                        "saml_id": "new_one",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == []
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "saml_id": {"info": "done", "value": "new_one"},
            "username": {"info": "done", "value": "test", "id": 2},
        }

    def json_upload_names_and_email_find_username(self) -> None:
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
                        "default_password": "new default password",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["data"] == {
            "id": 34,
            "first_name": {"value": "Max", "info": ImportState.DONE},
            "last_name": {"value": "Mustermann", "info": ImportState.DONE},
            "email": {"value": "test@ntvtn.de", "info": ImportState.DONE},
            "default_password": {"value": "new default password", "info": "done"},
            "username": {"value": "test", "info": "done", "id": 34},
        }

    def json_upload_names_and_email_generate_username(self) -> None:
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
        assert entry["data"]["first_name"] == {"value": "Max", "info": ImportState.DONE}
        assert entry["data"]["last_name"] == {
            "value": "Mustermann",
            "info": ImportState.DONE,
        }
        assert entry["data"]["username"] == {
            "value": "MaxMustermann1",
            "info": ImportState.GENERATED,
        }
        assert entry["data"]["default_password"]["info"] == ImportState.GENERATED

    def json_upload_with_complicated_names(self) -> None:
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "first_name": "One Two",
                        "last_name": "Three",
                    },
                    {
                        "first_name": "One-Two",
                        "last_name": "Three",
                    },
                    {
                        "first_name": "One",
                        "last_name": "Two Three",
                    },
                    {
                        "first_name": "One",
                        "last_name": "Two-Three",
                    },
                    {
                        "first_name": "One Two Thre",
                        "last_name": "e",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert [
            entry["data"]["username"]["value"] + " " + entry["data"]["username"]["info"]
            for entry in response.json["results"][0][0]["rows"]
        ] == [
            "OneTwoThree generated",
            "OneTwoThree1 generated",
            "OneTwoThree2 generated",
            "OneTwoThree3 generated",
            "OneTwoThree4 generated",
        ]

    def json_upload_generate_default_password(self) -> None:
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
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["data"].get("default_password")
        assert (
            import_preview["result"]["rows"][0]["data"]["default_password"]["info"]
            == ImportState.GENERATED
        )

    def json_upload_wrong_gender(self) -> None:
        self.set_models(
            {
                "organization/1": {"gender_ids": [1, 2, 3, 4]},
                "gender/1": {"name": "male"},
                "gender/2": {"name": "female"},
                "gender/3": {"name": "diverse"},
                "gender/4": {"name": "non-binary"},
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [{"username": "test", "gender": "veryveryveryverybad"}],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["data"]["gender"] == {
            "value": "veryveryveryverybad",
            "info": ImportState.WARNING,
        }
        assert (
            "Gender 'veryveryveryverybad' is not in the allowed gender list."
            in import_preview["result"]["rows"][0]["messages"]
        )

    def json_upload_wrong_gender_2(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"gender_ids": [1, 2, 3]},
                "gender/1": {"name": "dragon"},
                "gender/2": {"name": "lobster"},
                "gender/3": {"name": "snake"},
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [{"username": "test", "gender": "male"}],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["data"]["gender"] == {
            "value": "male",
            "info": ImportState.WARNING,
        }
        assert (
            "Gender 'male' is not in the allowed gender list."
            in import_preview["result"]["rows"][0]["messages"]
        )

    def json_upload_username_10_saml_id_11(self) -> None:
        self.set_models(
            {
                "user/10": {
                    "username": "user10",
                },
                "user/11": {
                    "username": "user11",
                    "saml_id": "saml_id11",
                },
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "user10",
                        "saml_id": "saml_id10",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["data"] == {
            "id": 10,
            "username": {"value": "user10", "info": "done", "id": 10},
            "saml_id": {"value": "saml_id10", "info": "new"},
            "default_password": {"value": "", "info": "warning"},
        }

    def json_upload_username_username_and_saml_id_found(self) -> None:
        self.set_models(
            {
                "user/11": {
                    "username": "user11",
                    "saml_id": "saml_id11",
                }
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "user11",
                        "saml_id": "saml_id11",
                        "default_vote_weight": "11.000000",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["data"] == {
            "id": 11,
            "username": {"value": "user11", "info": ImportState.DONE, "id": 11},
            "saml_id": {"value": "saml_id11", "info": ImportState.DONE},
            "default_vote_weight": {"value": "11.000000", "info": ImportState.DONE},
        }

    def json_upload_multiple_users(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "user2",
                    "password": "secret",
                    "default_password": "secret",
                    "can_change_own_password": True,
                    "default_vote_weight": "2.300000",
                },
                "user/3": {
                    "username": "user3",
                    "saml_id": "saml3",
                    "password": "secret",
                    "default_password": "secret",
                    "can_change_own_password": True,
                    "default_vote_weight": "3.300000",
                },
                "user/4": {
                    "username": "user4",
                    "first_name": "Martin",
                    "last_name": "Luther King",
                    "email": "mlk@america.com",
                    "password": "secret",
                    "default_password": "secret",
                    "can_change_own_password": True,
                    "default_vote_weight": "4.300000",
                },
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "user2",
                        "saml_id": "test_saml_id2",
                        "default_vote_weight": "2.345678",
                    },
                    {"saml_id": "saml3", "default_vote_weight": "3.345678"},
                    {
                        "first_name": "Martin",
                        "last_name": "Luther King",
                        "email": "mlk@america.com",
                        "default_vote_weight": "4.345678",
                    },
                    {
                        "username": "new_user5",
                        "default_vote_weight": "5.345678",
                        "saml_id": "saml5",
                    },
                    {
                        "saml_id": "new_saml6",
                        "default_vote_weight": "6.345678",
                    },
                    {
                        "first_name": "Joan",
                        "last_name": "Baez7",
                        "default_vote_weight": "7.345678",
                    },
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.WARNING
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Because this account is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides."
        ]
        assert import_preview["result"]["rows"][0]["data"] == {
            "id": 2,
            "saml_id": {"info": "new", "value": "test_saml_id2"},
            "username": {"id": 2, "info": "done", "value": "user2"},
            "default_password": {"info": "warning", "value": ""},
            "default_vote_weight": {"value": "2.345678", "info": ImportState.DONE},
        }

        assert import_preview["result"]["rows"][1]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][1]["messages"] == [
            "Because this account is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides."
        ]
        assert import_preview["result"]["rows"][1]["data"] == {
            "id": 3,
            "saml_id": {"info": ImportState.DONE, "value": "saml3"},
            "username": {"id": 3, "info": ImportState.DONE, "value": "user3"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "default_vote_weight": {"value": "3.345678", "info": ImportState.DONE},
        }

        assert import_preview["result"]["rows"][2]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][2]["messages"] == []
        assert import_preview["result"]["rows"][2]["data"] == {
            "id": 4,
            "email": {"value": "mlk@america.com", "info": ImportState.DONE},
            "username": {"id": 4, "info": "done", "value": "user4"},
            "last_name": {"value": "Luther King", "info": ImportState.DONE},
            "first_name": {"value": "Martin", "info": ImportState.DONE},
            "default_vote_weight": {"value": "4.345678", "info": ImportState.DONE},
        }

        assert import_preview["result"]["rows"][3]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][3]["messages"] == [
            "Because this account is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides."
        ]
        assert import_preview["result"]["rows"][3]["data"] == {
            "saml_id": {"info": "new", "value": "saml5"},
            "username": {"info": "done", "value": "new_user5"},
            "default_password": {"info": "warning", "value": ""},
            "default_vote_weight": {"value": "5.345678", "info": ImportState.DONE},
        }

        assert import_preview["result"]["rows"][4]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][4]["messages"] == [
            "Because this account is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides."
        ]
        assert import_preview["result"]["rows"][4]["data"] == {
            "saml_id": {"info": "new", "value": "new_saml6"},
            "username": {"info": "generated", "value": "new_saml6"},
            "default_password": {"info": "warning", "value": ""},
            "default_vote_weight": {"value": "6.345678", "info": ImportState.DONE},
        }

        assert import_preview["result"]["rows"][5]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][5]["messages"] == []
        default_password = import_preview["result"]["rows"][5]["data"].pop(
            "default_password"
        )
        assert default_password["info"] == ImportState.GENERATED
        assert default_password["value"]
        assert import_preview["result"]["rows"][5]["data"] == {
            "username": {"info": "generated", "value": "JoanBaez7"},
            "last_name": {"value": "Baez7", "info": ImportState.DONE},
            "first_name": {"value": "Joan", "info": ImportState.DONE},
            "default_vote_weight": {"value": "7.345678", "info": ImportState.DONE},
        }

    def json_upload_legacy_username(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "test user",
                },
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "test user",
                        "first_name": "test",
                    },
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0] == {
            "state": ImportState.DONE,
            "messages": [],
            "data": {
                "id": 2,
                "username": {"id": 2, "info": ImportState.DONE, "value": "test user"},
                "first_name": {"info": ImportState.DONE, "value": "test"},
            },
        }

    def json_upload_update_reference_via_two_attributes(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "test",
                    "default_vote_weight": "2.300000",
                    "saml_id": "old_one",
                }
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "test",
                        "saml_id": "old_one",
                        "default_vote_weight": "4.500000",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == []
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "saml_id": {"info": "done", "value": "old_one"},
            "username": {"info": "done", "value": "test", "id": 2},
            "default_vote_weight": {"info": "done", "value": "4.500000"},
        }

    def json_upload_set_member_number_in_existing_accounts(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "test1",
                    "default_vote_weight": "2.300000",
                },
                "user/3": {"username": "test2", "saml_id": "samLidman"},
                "user/4": {
                    "username": "test3",
                    "first_name": "Hasan",
                    "last_name": "Ame",
                    "email": "hasaN.ame@nd.email",
                },
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "test1",
                        "member_number": "new_one",
                    },
                    {
                        "saml_id": "samLidman",
                        "member_number": "another_new_1",
                    },
                    {
                        "first_name": "Hasan",
                        "last_name": "Ame",
                        "email": "hasaN.ame@nd.email",
                        "member_number": "UGuessedIt",
                    },
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == []
        row = import_preview["result"]["rows"][0]["data"]
        assert row == {
            "id": 2,
            "username": {"info": "done", "value": "test1", "id": 2},
            "member_number": {"info": "new", "value": "new_one"},
        }
        row = import_preview["result"]["rows"][1]["data"]
        assert row == {
            "id": 3,
            "username": {"info": "done", "value": "test2", "id": 3},
            "saml_id": {"info": "done", "value": "samLidman"},
            "member_number": {"info": "new", "value": "another_new_1"},
        }
        row = import_preview["result"]["rows"][2]["data"]
        assert row == {
            "id": 4,
            "username": {"info": "done", "value": "test3", "id": 4},
            "first_name": {"value": "Hasan", "info": ImportState.DONE},
            "last_name": {"value": "Ame", "info": ImportState.DONE},
            "email": {"info": "done", "value": "hasaN.ame@nd.email"},
            "member_number": {"info": "new", "value": "UGuessedIt"},
        }

    def json_upload_set_other_matching_criteria_in_existing_account_via_member_number(
        self,
    ) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "test",
                    "saml_id": "some_saml",
                    "first_name": "first",
                    "last_name": "last",
                    "default_vote_weight": "2.300000",
                    "member_number": "M3MNUM",
                    "default_password": "passworddd",
                    "password": "pass",
                }
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "newname",
                        "saml_id": "some_other_saml",
                        "first_name": "second",
                        "last_name": "second_to_last",
                        "member_number": "M3MNUM",
                        "email": "a.new@ma.il",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.WARNING
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Because this account is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides."
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "default_password": {"value": "", "info": "warning"},
            "username": {"info": "new", "value": "newname"},
            "saml_id": {"info": "new", "value": "some_other_saml"},
            "first_name": {"value": "second", "info": ImportState.DONE},
            "last_name": {"value": "second_to_last", "info": ImportState.DONE},
            "member_number": {"info": "done", "value": "M3MNUM", "id": 2},
            "email": {"info": "done", "value": "a.new@ma.il"},
        }

    def json_upload_add_member_number(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "test",
                    "default_vote_weight": "2.300000",
                    "member_number": "old_one",
                }
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "test",
                        "member_number": "old_one",
                        "default_vote_weight": "4.345678",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == []
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "member_number": {"info": "done", "value": "old_one", "id": 2},
            "username": {"info": "done", "value": "test"},
            "default_vote_weight": {"info": "done", "value": "4.345678"},
        }

    def json_upload_new_account_with_member_number(self) -> None:
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "newname",
                        "saml_id": "some_other_saml",
                        "first_name": "second",
                        "last_name": "second_to_last",
                        "member_number": "M3MNUM",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.WARNING
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Because this account is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides."
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "default_password": {"value": "", "info": "warning"},
            "username": {"info": "done", "value": "newname"},
            "saml_id": {"info": "new", "value": "some_other_saml"},
            "first_name": {"value": "second", "info": ImportState.DONE},
            "last_name": {"value": "second_to_last", "info": ImportState.DONE},
            "member_number": {"info": "done", "value": "M3MNUM"},
        }

    def json_upload_match_via_member_number_no_username(
        self,
    ) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "test",
                    "saml_id": "some_saml",
                    "first_name": "first",
                    "last_name": "last",
                    "default_vote_weight": "2.300000",
                    "member_number": "M3MNUM",
                    "default_password": "passworddd",
                    "password": "pass",
                }
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "member_number": "M3MNUM",
                        "email": "a.new@ma.il",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == []
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "username": {"info": "done", "value": "test"},
            "member_number": {"info": "done", "value": "M3MNUM", "id": 2},
            "email": {"info": "done", "value": "a.new@ma.il"},
        }

    def json_upload_match_via_member_number_no_username_or_other_data(
        self,
    ) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "test",
                    "saml_id": "some_saml",
                    "first_name": "first",
                    "last_name": "last",
                    "default_vote_weight": "2.300000",
                    "member_number": "M3MNUM",
                    "default_password": "passworddd",
                    "password": "pass",
                }
            }
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "member_number": "M3MNUM",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == []
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "username": {"info": "done", "value": "test"},
            "member_number": {"info": "done", "value": "M3MNUM", "id": 2},
        }

    def json_upload_set_home_committee(
        self, guest: bool | None = None, has_perm: bool = True
    ) -> None:
        self.create_committee(1, name="Home")
        if has_perm:
            self.set_committee_management_level([1])
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        date: dict[str, Any] = {"username": "Alice", "home_committee": "Home"}
        if guest is True:
            date["guest"] = "1"
        elif guest is False:
            date["guest"] = "0"
        response = self.request(
            "account.json_upload",
            {
                "data": [date],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][0]["messages"] == (
            []
            if has_perm
            else [
                "Account is updated, but changes to the following field(s) are not possible: home_committee, guest"
            ]
        )
        data = import_preview["result"]["rows"][0]["data"]
        assert data["username"] == {"info": ImportState.DONE, "value": "Alice"}
        assert data["home_committee"] == {
            "info": ImportState.DONE if has_perm else ImportState.REMOVE,
            "value": "Home",
            "id": 1,
        }
        if guest is None:
            assert data["guest"] == {
                "info": ImportState.GENERATED if has_perm else ImportState.REMOVE,
                "value": False,
            }
        else:
            assert data["guest"] == {
                "info": ImportState.DONE if has_perm else ImportState.REMOVE,
                "value": guest,
            }

    def json_upload_update_home_committee(
        self, old_perm: bool = True, new_perm: bool = True
    ) -> None:
        self.create_committee(1, name="Old home")
        self.create_committee(2, name="Home")
        alice_id = self.create_user("Alice", home_committee_id=1)
        if old_perm or new_perm:
            self.set_committee_management_level(
                ([1, 2] if new_perm else [1]) if old_perm else [2]
            )
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "username": "Alice",
                        "home_committee": "Home",
                        "first_name": "alice",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        if old_perm and new_perm:
            assert import_preview["result"]["rows"][0]["messages"] == []
        else:
            assert import_preview["result"]["rows"][0]["messages"] == [
                "Account is updated, but changes to the following field(s) are not possible: home_committee, guest"
            ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data["id"] == alice_id
        assert data["username"] == {
            "id": alice_id,
            "info": ImportState.DONE,
            "value": "Alice",
        }
        if old_perm and new_perm:
            assert data["home_committee"] == {
                "info": ImportState.DONE,
                "value": "Home",
                "id": 2,
            }
            assert data["guest"] == {"info": ImportState.GENERATED, "value": False}
        else:
            assert data["home_committee"] == {
                "info": ImportState.REMOVE,
                "value": "Home",
                "id": 2,
            }
            assert data["guest"] == {"info": ImportState.REMOVE, "value": False}

    def json_upload_set_guest_to_true(self) -> None:
        response = self.request(
            "account.json_upload",
            {
                "data": [{"username": "Alice", "guest": "1"}],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][0]["messages"] == [
            "If guest is set to true, any home_committee that was set will be removed."
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data["username"] == {"info": ImportState.DONE, "value": "Alice"}
        assert data["home_committee"] == {"info": ImportState.GENERATED, "value": None}
        assert data["guest"] == {"info": ImportState.DONE, "value": True}

    def json_upload_update_guest_true(
        self, with_home_committee: bool = False, has_home_committee_perms: bool = True
    ) -> None:
        if with_home_committee:
            self.create_committee(1, name="Home")
            alice_id = self.create_user("Alice", home_committee_id=1)
            if not has_home_committee_perms:
                self.set_organization_management_level(
                    OrganizationManagementLevel.CAN_MANAGE_USERS
                )
        else:
            has_home_committee_perms = True
            alice_id = self.create_user("Alice")
        response = self.request(
            "account.json_upload",
            {
                "data": [{"username": "Alice", "guest": "1", "first_name": "alice"}],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        messages = [
            "If guest is set to true, any home_committee that was set will be removed."
        ]
        if not has_home_committee_perms:
            messages.append(
                "Account is updated, but changes to the following field(s) are not possible: home_committee, guest"
            )
        assert import_preview["result"]["rows"][0]["messages"] == messages
        data = import_preview["result"]["rows"][0]["data"]
        assert data["id"] == alice_id
        assert data["username"] == {
            "info": ImportState.DONE,
            "value": "Alice",
            "id": alice_id,
        }
        assert data["home_committee"] == {
            "info": (
                ImportState.GENERATED
                if has_home_committee_perms
                else ImportState.REMOVE
            ),
            "value": None,
        }
        assert data["guest"] == {
            "info": (
                ImportState.DONE if has_home_committee_perms else ImportState.REMOVE
            ),
            "value": True,
        }

    def json_upload_update_guest_false_without_home_committee(self) -> None:
        alice_id = self.create_user("Alice")
        self.set_models({f"user/{alice_id}": {"guest": True}})
        response = self.request(
            "account.json_upload",
            {
                "data": [{"username": "Alice", "guest": "0"}],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == []
        data = import_preview["result"]["rows"][0]["data"]
        assert data["id"] == alice_id
        assert data["username"] == {
            "id": alice_id,
            "info": ImportState.DONE,
            "value": "Alice",
        }
        assert data["guest"] == {"info": ImportState.DONE, "value": False}
        assert "home_committee" not in data

    def json_upload_update_guest_false_with_home_committee(self) -> None:
        self.create_committee(1, name="Home")
        alice_id = self.create_user("Alice", home_committee_id=1)
        response = self.request(
            "account.json_upload",
            {
                "data": [{"username": "Alice", "guest": "0"}],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == []
        data = import_preview["result"]["rows"][0]["data"]
        assert data["id"] == alice_id
        assert data["username"] == {
            "id": alice_id,
            "info": ImportState.DONE,
            "value": "Alice",
        }
        assert data["guest"] == {"info": ImportState.DONE, "value": False}
        assert "home_committee" not in data

    def json_upload_update_guest_false_without_home_committee_perms(self) -> None:
        self.create_committee(1, name="Home")
        alice_id = self.create_user("Alice", home_committee_id=1)
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [{"username": "Alice", "guest": "0"}],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Account is updated, but changes to the following field(s) are not possible: guest"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data["id"] == alice_id
        assert data["username"] == {
            "info": ImportState.DONE,
            "value": "Alice",
            "id": alice_id,
        }
        assert data["guest"] == {"info": ImportState.REMOVE, "value": False}
        assert "home_committee" not in data

    def json_upload_update_home_committee_and_guest_false_no_perms_new(self) -> None:
        self.create_committee(1, name="Old home")
        self.create_committee(2, name="Home")
        alice_id = self.create_user("Alice", home_committee_id=1)
        self.set_committee_management_level([1])
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [{"username": "Alice", "home_committee": "Home", "guest": "0"}],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Account is updated, but changes to the following field(s) are not possible: home_committee, guest"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data["id"] == alice_id
        assert data["username"] == {
            "id": alice_id,
            "info": ImportState.DONE,
            "value": "Alice",
        }
        assert data["home_committee"] == {
            "info": ImportState.REMOVE,
            "value": "Home",
            "id": 2,
        }
        assert data["guest"] == {"info": ImportState.REMOVE, "value": False}

    def json_upload_with_gender_as_orga_admin(self) -> None:
        self.set_models(
            {
                "organization/1": {"gender_ids": [1, 2, 3, 4]},
                "gender/1": {"name": "male"},
                "gender/2": {"name": "female"},
                "gender/3": {"name": "diverse"},
                "gender/4": {"name": "non-binary"},
            }
        )
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        response = self.request(
            "account.json_upload",
            {
                "data": [{"username": "man", "gender": "male"}],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["data"]["gender"] == {
            "id": 1,
            "value": "male",
            "info": ImportState.DONE,
        }
        assert import_preview["result"]["rows"][0]["messages"] == []

    def json_upload_multiple_with_same_home_committee(self) -> None:
        self.create_committee(name="Entenhausen")
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "first_name": "Tick",
                        "username": "Huey",
                        "home_committee": "Entenhausen",
                        "default_password": "Quack1",
                    },
                    {
                        "first_name": "Trick",
                        "username": "Dewey",
                        "home_committee": "Entenhausen",
                        "default_password": "Quack2",
                    },
                    {
                        "first_name": "Track",
                        "username": "Louie",
                        "home_committee": "Entenhausen",
                        "default_password": "Quack3",
                    },
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "account"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][0]["messages"] == []
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "first_name": {"info": "done", "value": "Tick"},
            "username": {"info": "done", "value": "Huey"},
            "home_committee": {"info": "done", "value": "Entenhausen", "id": 1},
            "guest": {
                "info": "generated",
                "value": False,
            },
            "default_password": {
                "info": "done",
                "value": "Quack1",
            },
        }
        assert import_preview["result"]["rows"][1]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][1]["messages"] == []
        data = import_preview["result"]["rows"][1]["data"]
        assert data == {
            "first_name": {"info": "done", "value": "Trick"},
            "username": {"info": "done", "value": "Dewey"},
            "home_committee": {"info": "done", "value": "Entenhausen", "id": 1},
            "guest": {
                "info": "generated",
                "value": False,
            },
            "default_password": {
                "info": "done",
                "value": "Quack2",
            },
        }
        assert import_preview["result"]["rows"][2]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][2]["messages"] == []
        data = import_preview["result"]["rows"][2]["data"]
        assert data == {
            "first_name": {"info": "done", "value": "Track"},
            "username": {"info": "done", "value": "Louie"},
            "home_committee": {"info": "done", "value": "Entenhausen", "id": 1},
            "guest": {
                "info": "generated",
                "value": False,
            },
            "default_password": {
                "info": "done",
                "value": "Quack3",
            },
        }

    def json_upload_multiple_with_x(self) -> None:
        users: dict[str, dict[str, str | int]] = {
            "user/2": {
                "last_name": "Administratorr",
                "username": "superadmin",
                "default_vote_weight": "1.000000",
                "is_active": "1",
                "is_physical_person": "1",
            },
            "user/3": {
                "first_name": "Gustav",
                "last_name": "Gans",
                "email": "schwan@ntntv.de",
                "gender_id": 2,
                "username": "schwante",
                "default_password": "UWoPkunmfa",
                "is_active": "1",
                "is_physical_person": "1",
                "default_vote_weight": "1.000000",
            },
            "user/4": {
                "first_name": "bib",
                "last_name": "lib",
                "email": "bib.lib@intevation.de",
                "gender_id": 2,
                "username": "biblib",
                "default_password": "HBYwkTsZLGzNpCz",
                "is_active": "1",
                "is_physical_person": "1",
                "default_vote_weight": "1.000000",
            },
            "user/5": {
                "first_name": "Loki",
                "last_name": "Jötnar",
                "email": "loki@asen.sk",
                "gender_id": 4,
                "username": "witz",
                "default_password": "WquptS9VbL",
                "is_active": "1",
                "is_physical_person": "1",
                "default_vote_weight": "1.000000",
            },
        }
        self.set_models(
            {
                "gender/2": {"name": "female"},
                "gender/4": {"name": "non-binary"},
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                },
                **users,
            }
        )
        for fqid, user in users.items():
            id_ = id_from_fqid(fqid)
            if user.pop("gender_id", 0):
                user["gender"] = "female"
            if id_ != 3:
                self.set_organization_management_level(
                    OrganizationManagementLevel.SUPERADMIN, id_
                )
            del user["default_vote_weight"]
        users["user/4"]["last_name"] = "library"
        users["user/5"]["email"] = "loki@intevation.de"
        users["user/5"]["gender"] = "non-binary"
        response = self.request("account.json_upload", {"data": list(users.values())})
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "account"
        for fqid, user in users.items():
            id_ = id_from_fqid(fqid)
            row = id_ - 2
            assert import_preview["result"]["rows"][row]["state"] == ImportState.DONE
            if id_ != 3:
                import_state = ImportState.REMOVE
                if id_ == 2:
                    assert import_preview["result"]["rows"][row]["messages"] == [
                        "Account is updated, but changes to the following field(s) are not possible: last_name, username, is_active, is_physical_person"
                    ]
                else:
                    assert import_preview["result"]["rows"][row]["messages"] == [
                        "Account is updated, but changes to the following field(s) are not possible: first_name, last_name, email, username, is_active, is_physical_person, gender_id, default_password"
                    ]
            else:
                import_state = ImportState.DONE
                assert import_preview["result"]["rows"][row]["messages"] == []
            expected_data = {
                "id": id_,
                "first_name": {"info": import_state, "value": user.get("first_name")},
                "last_name": {"info": import_state, "value": user.get("last_name")},
                "username": {
                    "info": import_state,
                    "value": user.get("username"),
                    "id": id_,
                },
                "email": {
                    "info": import_state,
                    "value": user.get("email"),
                },
                "default_password": {
                    "value": user.get("default_password"),
                    "info": import_state,
                },
                "is_active": {"info": import_state, "value": True},
                "is_physical_person": {"info": import_state, "value": True},
                "gender": {
                    "info": import_state,
                    "value": user.get("gender"),
                    "id": 2 if user.get("gender") == "female" else 4,
                },
            }
            if id_ == 2:
                del expected_data["first_name"]
                del expected_data["email"]
                del expected_data["gender"]
                del expected_data["default_password"]
            assert import_preview["result"]["rows"][row]["data"] == expected_data
