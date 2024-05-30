from time import time

from openslides_backend.action.mixins.import_mixins import ImportState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.patterns import fqid_from_collection_and_id
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class AccountJsonUpload(BaseActionTestCase):
    def test_json_upload_simple(self) -> None:
        start_time = int(time())
        response = self.request(
            "account.json_upload",
            {
                "data": [
                    {
                        "organization/1": {
                            "genders": ["male", "female", "diverse", "non-binary"]
                        },
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
                "default_vote_weight": {"value": "1.120000", "info": ImportState.DONE},
                "gender": {"value": "female", "info": ImportState.DONE},
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
                "Cannot generate username. Missing one of first_name, last_name or a unique member_number."
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
                    "first_name": "Max",
                    "last_name": "Mustermann",
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
                    "first_name": "Max",
                    "last_name": "Mustermann",
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
                    "first_name": "John",
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
            "first_name": "Max",
            "last_name": "Mustermann",
            "email": {"value": "max@mustermann.org", "info": ImportState.DONE},
            "default_vote_weight": {"value": "1.000000", "info": ImportState.DONE},
            "username": {"value": "test", "info": ImportState.DONE, "id": 3},
        }
        assert result["rows"][1]["messages"] == ["Found more users with name and email"]
        assert result["rows"][1]["state"] == ImportState.ERROR
        assert result["rows"][1]["data"] == {
            "id": 3,
            "first_name": "Max",
            "last_name": "Mustermann",
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
            "first_name": "Max",
            "last_name": "Mustermann",
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
            "first_name": "Fritz",
            "last_name": "Chen",
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
            "Cannot generate username. Missing one of first_name, last_name or a unique member_number."
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data["username"] == {"info": "generated", "value": ""}
        assert data["member_number"] == {"info": "done", "value": "M3MNUM"}


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
        assert import_preview["result"]["rows"][2]["data"]["last_name"] == "ml_id2"
        assert import_preview["result"]["rows"][2]["data"]["first_name"] == "test_sa"

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
            "first_name": "Max",
            "last_name": "Mustermann",
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
        assert entry["data"]["first_name"] == "Max"
        assert entry["data"]["last_name"] == "Mustermann"
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
            {"organization/1": {"genders": ["male", "female", "diverse", "non-binary"]}}
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
            {ONE_ORGANIZATION_FQID: {"genders": ["dragon", "lobster", "snake"]}}
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
            "last_name": "Luther King",
            "first_name": "Martin",
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
            "last_name": "Baez7",
            "first_name": "Joan",
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
                "first_name": "test",
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
            "first_name": "Hasan",
            "last_name": "Ame",
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
            "first_name": "second",
            "last_name": "second_to_last",
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
            "first_name": "second",
            "last_name": "second_to_last",
            "member_number": {"info": "done", "value": "M3MNUM"},
        }

    def json_upload_new_account_with_only_member_number(self) -> None:
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
        assert import_preview["result"]["rows"][0]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][0]["messages"] == []
        data = import_preview["result"]["rows"][0]["data"]
        assert data["username"] == {"info": "generated", "value": "M3MNUM"}
        assert data["member_number"] == {"info": "done", "value": "M3MNUM"}

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
