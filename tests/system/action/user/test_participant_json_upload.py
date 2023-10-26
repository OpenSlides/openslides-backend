from time import time

from openslides_backend.action.mixins.import_mixins import ImportState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.patterns import fqid_from_collection_and_id
from tests.system.action.base import BaseActionTestCase


class ParticipantJsonUpload(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {"name": "test", "group_ids": [1]},
                "group/1": {"name": "testgroup", "meeting_id": 1},
            }
        )

    def test_json_upload_simple(self) -> None:
        start_time = int(time())
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "test",
                        "default_password": "secret",
                        "is_active": "1",
                        "is_physical_person": "F",
                        "number": "strange number",
                        "structure_level": "CEO",
                        "vote_weight": "1.12",
                        "comment": "my comment",
                        "is_present": "0",
                        "groups": ["testgroup", "notfound_group1", "notfound_group2"],
                        "wrong": 15,
                    }
                ],
            },
        )
        end_time = int(time())
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [
                "Following groups were not found: 'notfound_group1, notfound_group2'"
            ],
            "data": {
                "username": {"value": "test", "info": ImportState.DONE},
                "default_password": {"value": "secret", "info": ImportState.DONE},
                "is_active": True,
                "is_physical_person": False,
                "number": "strange number",
                "structure_level": "CEO",
                "vote_weight": "1.120000",
                "comment": "my comment",
                "is_present": False,
                "groups": [
                    {"value": "testgroup", "info": "done", "id": 1},
                    {"value": "notfound_group1", "info": ImportState.WARNING},
                    {"value": "notfound_group2", "info": ImportState.WARNING},
                ],
            },
        }
        import_preview_id = response.json["results"][0][0].get("id")
        import_preview_fqid = fqid_from_collection_and_id(
            "import_preview", import_preview_id
        )
        import_preview = self.assert_model_exists(
            import_preview_fqid, {"name": "participant", "state": ImportState.WARNING}
        )
        assert start_time <= import_preview["created"] <= end_time

    def test_json_upload_empty_data(self) -> None:
        response = self.request(
            "participant.json_upload",
            {"data": [], "meeting_id": 1},
        )
        self.assert_status_code(response, 400)
        assert "data.data must contain at least 1 items" in response.json["message"]

    def test_json_upload_without_meeting(self) -> None:
        response = self.request(
            "participant.json_upload",
            {"data": []},
        )
        self.assert_status_code(response, 400)
        assert (
            "data must contain ['data', 'meeting_id'] properties"
            in response.json["message"]
        )

    def test_json_upload_not_existing_meeting(self) -> None:
        response = self.request(
            "participant.json_upload",
            {"data": [{"username": "test"}], "meeting_id": 111},
        )
        self.assert_status_code(response, 400)
        assert (
            "Participant import try to use not existing meeting 111"
            in response.json["message"]
        )

    def test_json_upload_without_names_error(self) -> None:
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "number": "strange number",
                        "groups": "testgroup",
                    }
                ],
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
                "groups": [{"value": "testgroup", "info": ImportState.DONE, "id": 1}],
                "number": "strange number",
            },
        }

    def test_json_upload_no_default_group(self) -> None:
        response = self.request(
            "participant.json_upload",
            {"data": [{"username": "testuser"}], "meeting_id": 1},
        )
        self.assert_status_code(response, 400)
        assert (
            "No valid group given in import and no default_group for meeting defined!"
            in response.json["message"]
        )

    def test_json_upload_results(self) -> None:
        self.set_models({"group/1": {"default_group_for_meeting_id": 1}})
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [{"username": "test", "default_password": "secret"}],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "import_preview/1",
            {
                "name": "participant",
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
                                "groups": [
                                    {
                                        "id": 1,
                                        "info": ImportState.GENERATED,
                                        "value": "testgroup",
                                    }
                                ],
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
                {"property": "email", "type": "string"},
                {"property": "username", "type": "string", "is_object": True},
                {"property": "gender", "type": "string"},
                {"property": "pronoun", "type": "string"},
                {"property": "saml_id", "type": "string", "is_object": True},
                {"property": "structure_level", "type": "string"},
                {"property": "number", "type": "string"},
                {"property": "vote_weight", "type": "decimal"},
                {"property": "comment", "type": "string"},
                {"property": "is_present", "type": "boolean"},
                {
                    "property": "groups",
                    "type": "string",
                    "is_object": True,
                    "is_list": True,
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
                        "groups": [
                            {
                                "id": 1,
                                "info": ImportState.GENERATED,
                                "value": "testgroup",
                            }
                        ],
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

    def test_json_upload_no_permission(self) -> None:
        self.base_permission_test(
            {},
            "participant.json_upload",
            {"meeting_id": 1, "data": [{"username": "test"}]},
        )

    def test_json_upload_permission(self) -> None:
        self.base_permission_test(
            {},
            "participant.json_upload",
            {"meeting_id": 1, "data": [{"username": "test"}]},
            OrganizationManagementLevel.CAN_MANAGE_USERS,
        )


class ParticipantJsonUploadForUseInImport(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(1)
        self.create_meeting(4)

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
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "saml_id": "test_saml_id",
                        "default_password": "test2",
                        "groups": ["group1"],
                    },
                    {
                        "username": "test_saml_id1",
                        "groups": ["group1", "group2", "group3", "group4"],
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
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Will remove password and default_password and forbid changing your OpenSlides password."
        ]
        assert import_preview["result"]["rows"][0]["state"] == ImportState.NEW
        data0 = import_preview["result"]["rows"][0]["data"]
        assert data0 == {
            "saml_id": {"info": "new", "value": "test_saml_id"},
            "username": {"info": "generated", "value": "test_saml_id2"},
            "default_password": {"info": "warning", "value": ""},
            "groups": [{"value": "group1", "info": ImportState.DONE, "id": 1}],
        }

        assert import_preview["result"]["rows"][1]["messages"] == [
            "Following groups were not found: 'group4'"
        ]
        assert import_preview["result"]["rows"][1]["data"]["username"] == {
            "info": "done",
            "value": "test_saml_id1",
        }
        assert import_preview["result"]["rows"][1]["data"]["groups"] == [
            {"value": "group1", "info": ImportState.DONE, "id": 1},
            {"value": "group2", "info": ImportState.DONE, "id": 2},
            {"value": "group3", "info": ImportState.DONE, "id": 3},
            {"value": "group4", "info": ImportState.WARNING},
        ]

        assert import_preview["result"]["rows"][2]["messages"] == []
        assert import_preview["result"]["rows"][2]["data"]["username"] == {
            "info": "generated",
            "value": "test_saml_id21",
        }
        assert import_preview["result"]["rows"][2]["data"]["last_name"] == "ml_id2"
        assert import_preview["result"]["rows"][2]["data"]["first_name"] == "test_sa"
        assert import_preview["result"]["rows"][2]["data"]["groups"] == [
            {"value": "group1", "info": ImportState.GENERATED, "id": 1}
        ]

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
            "participant.json_upload",
            {
                "meeting_id": 1,
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
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Will remove password and default_password and forbid changing your OpenSlides password."
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "saml_id": {"info": "new", "value": "test_saml_id"},
            "username": {"info": "done", "value": "test", "id": 2},
            "default_password": {"info": "warning", "value": ""},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

    def json_upload_update_saml_id_in_existing_account(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "username": "test",
                    "saml_id": "old_one",
                }
            }
        )
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
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
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == []
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "saml_id": {"info": "done", "value": "new_one"},
            "username": {"info": "done", "value": "test", "id": 2},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

    def json_upload_names_and_email_find_add_meeting_data(self) -> None:
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
        fix_fields = {
            "first_name": "Max",
            "last_name": "Mustermann",
            "email": "test@ntvtn.de",
            "structure_level": "meeting1 structure level",
            "number": "meeting1 number",
            "comment": "meeting1 comment",
        }
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "default_password": "new default password",
                        "vote_weight": "1.456",
                        "is_present": "f",
                        **fix_fields,
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["data"] == {
            "id": 34,
            "default_password": {"value": "new default password", "info": "done"},
            "username": {"value": "test", "info": "done", "id": 34},
            "vote_weight": "1.456000",
            "is_present": False,
            "groups": [{"value": "group1", "info": "generated", "id": 1}],
            **fix_fields,
        }

    def json_upload_names_generate_username_password_create_meeting(self) -> None:
        self.set_models(
            {
                "user/34": {
                    "username": "MaxMustermann",
                    "first_name": "Max",
                    "last_name": "Mustermann",
                }
            }
        )

        fix_fields = {
            "first_name": "Max",
            "last_name": "Mustermann",
            "structure_level": "meeting1 structure level",
            "number": "meeting1 number",
            "comment": "meeting1 comment",
        }
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [{"vote_weight": "1.456", "is_present": "0", **fix_fields}],
            },
        )
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.NEW
        for key in fix_fields.keys():
            assert entry["data"][key] == fix_fields[key]
        assert entry["data"]["username"] == {
            "value": "MaxMustermann1",
            "info": ImportState.GENERATED,
        }
        assert entry["data"]["default_password"]["info"] == ImportState.GENERATED
        assert entry["data"]["vote_weight"] == "1.456000"
        assert entry["data"]["is_present"] is False

    def json_upload_username_10_saml_id_11_update_meeting(self) -> None:
        self.set_models(
            {
                "user/10": {
                    "username": "user10",
                    "meeting_user_ids": [110],
                    "is_present_in_meeting_ids": [1],
                },
                "meeting/1": {
                    "present_user_ids": [10],
                },
                "meeting_user/110": {
                    "meeting_id": 1,
                    "user_id": 10,
                    "structure_level": "old sl",
                    "number": "old number",
                    "comment": "old comment",
                },
                "user/11": {
                    "username": "user11",
                    "saml_id": "saml_id11",
                },
            }
        )
        fix_fields = {
            "structure_level": "new sl",
            "number": "new number",
            "comment": "new comment",
        }
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "user10",
                        "saml_id": "saml_id10",
                        "is_present": "0",
                        "vote_weight": "2.8",
                        **fix_fields,
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
            "is_present": False,
            "vote_weight": "2.800000",
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
            **fix_fields,
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
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "user11",
                        "saml_id": "saml_id11",
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
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
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
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "user2",
                        "saml_id": "test_saml_id2",
                    },
                    {"saml_id": "saml3", "default_vote_weight": "3.345678"},
                    {
                        "first_name": "Martin",
                        "last_name": "Luther King",
                        "email": "mlk@america.com",
                    },
                    {
                        "username": "new_user5",
                        "saml_id": "saml5",
                    },
                    {
                        "saml_id": "new_saml6",
                    },
                    {
                        "first_name": "Joan",
                        "last_name": "Baez7",
                    },
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.WARNING
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Will remove password and default_password and forbid changing your OpenSlides password."
        ]
        assert import_preview["result"]["rows"][0]["data"] == {
            "id": 2,
            "saml_id": {"info": "new", "value": "test_saml_id2"},
            "username": {"id": 2, "info": "done", "value": "user2"},
            "default_password": {"info": "warning", "value": ""},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

        assert import_preview["result"]["rows"][1]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][1]["messages"] == [
            "Will remove password and default_password and forbid changing your OpenSlides password."
        ]
        assert import_preview["result"]["rows"][1]["data"] == {
            "id": 3,
            "saml_id": {"info": ImportState.DONE, "value": "saml3"},
            "username": {"id": 3, "info": ImportState.DONE, "value": "user3"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

        assert import_preview["result"]["rows"][2]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][2]["messages"] == []
        assert import_preview["result"]["rows"][2]["data"] == {
            "id": 4,
            "email": "mlk@america.com",
            "username": {"id": 4, "info": "done", "value": "user4"},
            "last_name": "Luther King",
            "first_name": "Martin",
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

        assert import_preview["result"]["rows"][3]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][3]["messages"] == [
            "Will remove password and default_password and forbid changing your OpenSlides password."
        ]
        assert import_preview["result"]["rows"][3]["data"] == {
            "saml_id": {"info": "new", "value": "saml5"},
            "username": {"info": "done", "value": "new_user5"},
            "default_password": {"info": "warning", "value": ""},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

        assert import_preview["result"]["rows"][4]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][4]["messages"] == [
            "Will remove password and default_password and forbid changing your OpenSlides password."
        ]
        assert import_preview["result"]["rows"][4]["data"] == {
            "saml_id": {"info": "new", "value": "new_saml6"},
            "username": {"info": "generated", "value": "new_saml6"},
            "default_password": {"info": "warning", "value": ""},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
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
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }
