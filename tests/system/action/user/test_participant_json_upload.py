from time import time

from openslides_backend.action.mixins.import_mixins import ImportState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.patterns import fqid_from_collection_and_id
from tests.system.action.base import BaseActionTestCase


class ParticipantJsonUpload(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "organization/1": {
                    "genders": ["male", "female", "diverse", "non-binary"]
                },
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
                "is_active": {"value": True, "info": ImportState.DONE},
                "is_physical_person": {"value": False, "info": ImportState.DONE},
                "number": {"value": "strange number", "info": ImportState.DONE},
                "structure_level": {"value": "CEO", "info": ImportState.DONE},
                "vote_weight": {"value": "1.120000", "info": ImportState.DONE},
                "comment": {"value": "my comment", "info": ImportState.DONE},
                "is_present": {"value": False, "info": ImportState.DONE},
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
        assert "data must contain ['meeting_id'] properties" in response.json["message"]

    def test_json_upload_not_existing_meeting(self) -> None:
        response = self.request(
            "participant.json_upload",
            {"data": [{"username": "test"}], "meeting_id": 111},
        )
        self.assert_status_code(response, 400)
        assert (
            "Participant import tries to use non-existent meeting 111"
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
                "number": {"value": "strange number", "info": ImportState.DONE},
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
                    "meeting_id": 1,
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
                {"property": "title", "type": "string", "is_object": True},
                {"property": "first_name", "type": "string", "is_object": True},
                {"property": "last_name", "type": "string", "is_object": True},
                {"property": "is_active", "type": "boolean", "is_object": True},
                {
                    "property": "is_physical_person",
                    "type": "boolean",
                    "is_object": True,
                },
                {"property": "default_password", "type": "string", "is_object": True},
                {"property": "email", "type": "string", "is_object": True},
                {"property": "username", "type": "string", "is_object": True},
                {"property": "gender", "type": "string", "is_object": True},
                {"property": "pronoun", "type": "string", "is_object": True},
                {"property": "saml_id", "type": "string", "is_object": True},
                {"property": "structure_level", "type": "string", "is_object": True},
                {"property": "number", "type": "string", "is_object": True},
                {"property": "vote_weight", "type": "decimal", "is_object": True},
                {"property": "comment", "type": "string", "is_object": True},
                {"property": "is_present", "type": "boolean", "is_object": True},
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
            Permissions.User.CAN_MANAGE,
        )

    def test_json_upload_names_and_email_find_add_meeting_data(self) -> None:
        self.set_models(
            {
                "user/34": {
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "email": "test@ntvtn.de",
                    "username": "test",
                },
                "group/1": {"default_group_for_meeting_id": 1},
            }
        )
        fix_fields = {
            "first_name": "Max",
            "last_name": "Mustermann",
            "email": "test@ntvtn.de",
            "structure_level": "meeting1 structure level",
            "number": "meeting1 number",
            "comment": "meeting1 comment",
            "gender": "male",
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
        assert row["data"]["id"] == 34
        assert row["data"]["default_password"] == {
            "value": "new default password",
            "info": "done",
        }
        assert row["data"]["username"] == {"value": "test", "info": "done", "id": 34}
        assert row["data"]["vote_weight"] == {"value": "1.456000", "info": "done"}
        assert row["data"]["is_present"] == {"value": False, "info": "done"}
        assert row["data"]["gender"] == {"value": "male", "info": "done"}
        assert row["data"]["groups"] == [
            {"value": "testgroup", "info": "generated", "id": 1}
        ]
        for key in fix_fields.keys():
            assert row["data"][key]["value"] == fix_fields[key]

    def test_json_upload_names_generate_username_password_create_meeting(self) -> None:
        self.set_models(
            {
                "user/34": {
                    "username": "MaxMustermann",
                    "first_name": "Max",
                    "last_name": "Mustermann",
                },
                "group/1": {"default_group_for_meeting_id": 1},
            }
        )

        fix_fields = {
            "first_name": "Max",
            "last_name": "Mustermann",
            "structure_level": "meeting1 structure level",
            "gender": "notAGender",
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
            assert entry["data"][key]["value"] == fix_fields[key]
        assert entry["data"]["username"] == {
            "value": "MaxMustermann1",
            "info": ImportState.GENERATED,
        }
        assert entry["data"]["default_password"]["info"] == ImportState.GENERATED
        assert entry["data"]["vote_weight"] == {
            "value": "1.456000",
            "info": ImportState.DONE,
        }
        assert entry["data"]["structure_level"] == {
            "value": "meeting1 structure level",
            "info": ImportState.DONE,
        }
        assert entry["data"]["is_present"] == {"value": False, "info": ImportState.DONE}
        assert entry["data"]["groups"] == [
            {"value": "testgroup", "info": "generated", "id": 1}
        ]
        assert entry["data"]["gender"] == {
            "value": "notAGender",
            "info": ImportState.WARNING,
        }
        assert (
            "Gender 'notAGender' is not in the allowed gender list."
            in entry["messages"]
        )

    def test_json_upload_invalid_vote_weight(self) -> None:
        self.set_models({"group/1": {"default_group_for_meeting_id": 1}})
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "first_name": "Max",
                        "last_name": "Mustermann",
                        "email": "max@mustermann.org",
                        "vote_weight": "0",
                        "default_password": "halloIchBinMax",
                    },
                ],
            },
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.ERROR
        assert result["rows"][0]["messages"] == [
            "vote_weight must be bigger than or equal to 0.000001."
        ]
        assert result["rows"][0]["state"] == ImportState.ERROR
        assert result["rows"][0]["data"] == {
            "first_name": {"value": "Max", "info": ImportState.DONE},
            "last_name": {"value": "Mustermann", "info": ImportState.DONE},
            "email": {"value": "max@mustermann.org", "info": ImportState.DONE},
            "vote_weight": {"value": "0.000000", "info": ImportState.ERROR},
            "username": {"value": "MaxMustermann", "info": ImportState.GENERATED},
            "default_password": {"value": "halloIchBinMax", "info": ImportState.DONE},
            "groups": [{"id": 1, "info": "generated", "value": "testgroup"}],
        }


class ParticipantJsonUploadForUseInImport(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(1)
        self.create_meeting(4)

    def json_upload_invalid_vote_weight_with_remove(self) -> None:
        self.set_models(
            {
                "user/1": {"organization_management_level": "can_manage_users"},
                "user/2": {
                    "meeting_user_ids": [12],
                    "username": "wilhelm",
                    "meeting_ids": [1],
                },
                "meeting_user/12": {"meeting_id": 1, "group_ids": [1], "user_id": 2},
            }
        )
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "wilhelm",
                        "first_name": "Wilhelm",
                        "last_name": "Aberhatnurhut",
                        "email": "will@helm.hut",
                        "vote_weight": "0",
                        "default_password": "123",
                    },
                ],
            },
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.DONE
        assert (
            "vote_weight must be bigger than or equal to 0.000001."
            not in result["rows"][0]["messages"]
        )
        assert result["rows"][0]["state"] == ImportState.DONE
        assert result["rows"][0]["data"] == {
            "id": 2,
            "first_name": {"value": "Wilhelm", "info": ImportState.DONE},
            "last_name": {"value": "Aberhatnurhut", "info": ImportState.DONE},
            "email": {"value": "will@helm.hut", "info": ImportState.DONE},
            "vote_weight": {"value": "0.000000", "info": ImportState.REMOVE},
            "username": {"id": 2, "value": "wilhelm", "info": ImportState.DONE},
            "default_password": {"value": "123", "info": ImportState.DONE},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

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
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides."
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
        assert import_preview["result"]["rows"][2]["data"]["last_name"] == {
            "value": "ml_id2",
            "info": "done",
        }
        assert import_preview["result"]["rows"][2]["data"]["first_name"] == {
            "value": "test_sa",
            "info": "done",
        }
        assert import_preview["result"]["rows"][2]["data"]["groups"] == [
            {"value": "group1", "info": ImportState.GENERATED, "id": 1}
        ]

    def json_upload_set_saml_id_in_existing_participant(self) -> None:
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
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides."
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "saml_id": {"info": "new", "value": "test_saml_id"},
            "username": {"info": "done", "value": "test", "id": 2},
            "default_password": {"info": "warning", "value": ""},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

    def json_upload_update_saml_id_in_existing_participant(self) -> None:
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

    def json_upload_username_set_saml_id_remove_presence(self) -> None:
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
            "is_present": {"value": False, "info": "done"},
            "vote_weight": {"value": "2.800000", "info": "done"},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
            **{
                k: {"value": v, "info": ImportState.DONE} for k, v in fix_fields.items()
            },
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
                    "meeting_user_ids": [31, 34],
                },
                "meeting_user/31": {
                    "user_id": 3,
                    "meeting_id": 1,
                    "group_ids": [1, 2],
                    "vote_weight": "3.310000",
                },
                "meeting_user/34": {
                    "user_id": 3,
                    "meeting_id": 4,
                    "group_ids": [5],
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
                "group/1": {
                    "meeting_id": 1,
                    "meeting_user_ids": [31],
                },
                "group/2": {
                    "meeting_id": 1,
                    "meeting_user_ids": [31],
                },
                "group/5": {
                    "meeting_id": 4,
                    "meeting_user_ids": [34],
                },
                "group/7": {
                    "meeting_id": 1,
                    "name": "group7M1",
                },
                "meeting/1": {"meeting_user_ids": [31], "group_ids": [1, 2, 3, 7]},
                "meeting/4": {"meeting_user_ids": [34]},
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
                        "groups": ["group3", "group4"],
                    },
                    {
                        "saml_id": "saml3",
                        "vote_weight": "3.345678",
                        "groups": ["group3"],
                    },
                    {
                        "first_name": "Martin",
                        "last_name": "Luther King",
                        "email": "mlk@america.com",
                        "groups": ["group4"],
                    },
                    {
                        "username": "new_user5",
                        "saml_id": "saml5",
                    },
                    {"saml_id": "new_saml6", "groups": ["group4"], "is_present": "1"},
                    {
                        "first_name": "Joan",
                        "last_name": "Baez7",
                        "groups": ["group2", "group4", "unknown", "group7M1"],
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
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Following groups were not found: 'group4'",
        ]
        assert import_preview["result"]["rows"][0]["data"] == {
            "id": 2,
            "saml_id": {"info": "new", "value": "test_saml_id2"},
            "username": {"id": 2, "info": "done", "value": "user2"},
            "default_password": {"info": "warning", "value": ""},
            "groups": [
                {"id": 3, "info": "done", "value": "group3"},
                {"info": "warning", "value": "group4"},
            ],
        }

        assert import_preview["result"]["rows"][1]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][1]["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides."
        ]
        assert import_preview["result"]["rows"][1]["data"] == {
            "id": 3,
            "saml_id": {"info": ImportState.DONE, "value": "saml3"},
            "username": {"id": 3, "info": ImportState.DONE, "value": "user3"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "groups": [{"id": 3, "info": "done", "value": "group3"}],
            "vote_weight": {"info": ImportState.DONE, "value": "3.345678"},
        }

        assert import_preview["result"]["rows"][2]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][2]["messages"] == [
            "Following groups were not found: 'group4'"
        ]
        assert import_preview["result"]["rows"][2]["data"] == {
            "id": 4,
            "email": {"value": "mlk@america.com", "info": ImportState.DONE},
            "username": {"id": 4, "info": "done", "value": "user4"},
            "last_name": {"value": "Luther King", "info": ImportState.DONE},
            "first_name": {"value": "Martin", "info": ImportState.DONE},
            "groups": [
                {"info": "warning", "value": "group4"},
                {"id": 1, "info": "generated", "value": "group1"},
            ],
        }

        assert import_preview["result"]["rows"][3]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][3]["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides."
        ]
        assert import_preview["result"]["rows"][3]["data"] == {
            "saml_id": {"info": "new", "value": "saml5"},
            "username": {"info": "done", "value": "new_user5"},
            "default_password": {"info": "warning", "value": ""},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

        assert import_preview["result"]["rows"][4]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][4]["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Following groups were not found: 'group4'",
        ]
        assert import_preview["result"]["rows"][4]["data"] == {
            "saml_id": {"info": "new", "value": "new_saml6"},
            "username": {"info": "generated", "value": "new_saml6"},
            "default_password": {"info": "warning", "value": ""},
            "is_present": {"info": "done", "value": True},
            "groups": [
                {"info": "warning", "value": "group4"},
                {"id": 1, "info": "generated", "value": "group1"},
            ],
        }

        assert import_preview["result"]["rows"][5]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][5]["messages"] == [
            "Following groups were not found: 'group4, unknown'"
        ]
        default_password = import_preview["result"]["rows"][5]["data"].pop(
            "default_password"
        )
        assert default_password["info"] == ImportState.GENERATED
        assert default_password["value"]
        assert import_preview["result"]["rows"][5]["data"] == {
            "username": {"info": "generated", "value": "JoanBaez7"},
            "last_name": {"value": "Baez7", "info": ImportState.DONE},
            "first_name": {"value": "Joan", "info": ImportState.DONE},
            "groups": [
                {"id": 2, "info": "done", "value": "group2"},
                {"info": "warning", "value": "group4"},
                {"info": "warning", "value": "unknown"},
                {"id": 7, "info": "done", "value": "group7M1"},
            ],
        }

    def json_upload_with_complicated_names(self) -> None:
        response = self.request(
            "participant.json_upload",
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
                ],
                "meeting_id": 1,
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

    def json_upload_not_sufficient_field_permission_update(self) -> None:
        """try to change users first_name, but missing rights for user_scope committee"""
        self.set_models(
            {
                "user/1": {"organization_management_level": None},
                "user/2": {
                    "username": "user2",
                    "first_name": "John",
                    "meeting_user_ids": [11, 44],
                    "meeting_ids": [1, 4],
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
                    "default_password": "secret",
                    "can_change_own_password": True,
                    "password": "secretcrypted",
                },
                "committee/60": {"meeting_ids": [1, 4]},
                "meeting/1": {"meeting_user_ids": [11]},
                "meeting/4": {"meeting_user_ids": [44], "committee_id": 60},
                "meeting_user/11": {"meeting_id": 1, "user_id": 2, "group_ids": [1]},
                "meeting_user/44": {"meeting_id": 4, "user_id": 2, "group_ids": [5]},
                "group/1": {"meeting_user_ids": [11]},
                "group/5": {"meeting_user_ids": [44]},
            }
        )
        self.set_user_groups(1, [3])
        self.add_group_permissions(3, [Permissions.User.CAN_MANAGE])

        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "user2",  # group A, will be removed
                        "first_name": "Jim",  # group A, will be removed
                        "vote_weight": "1.23456",  # group B
                        "groups": ["group1", "group2", "group3", "group4"],  # group C
                        "committee_management_ids": [1],  # group D, not in payload
                        "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,  # group E, # group D, not in payload
                        "saml_id": "saml_id1",  # group E, will be removed
                        "default_password": "def_password",  # group F, will be removed
                        "is_demo_user": True,  # group G
                    }
                ],
            },
        )

        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Following groups were not found: 'group4'",
            "Following fields were removed from payload, because the user has no permissions to change them: username, first_name, saml_id, default_password",
        ]
        assert row["data"] == {
            "id": 2,
            "username": {"value": "user2", "info": "remove", "id": 2},
            "first_name": {"value": "Jim", "info": "remove"},
            "vote_weight": {"value": "1.234560", "info": "done"},
            "saml_id": {"value": "saml_id1", "info": "remove"},
            "default_password": {"value": "", "info": "remove"},
            "groups": [
                {"value": "group1", "info": "done", "id": 1},
                {"value": "group2", "info": "done", "id": 2},
                {"value": "group3", "info": "done", "id": 3},
                {"value": "group4", "info": "warning"},
            ],
        }

    def json_upload_sufficient_field_permission_create(self) -> None:
        self.update_model("user/1", {"organization_management_level": None})
        self.set_user_groups(1, [3])
        self.add_group_permissions(3, [Permissions.User.CAN_MANAGE])

        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "user2",
                        "first_name": "Jim",  # group A
                        "vote_weight": "1.23456",  # group B
                        "groups": ["group1", "group2", "group3", "group4"],  # group C
                        "committee_management_ids": [1],  # group D, not in payload
                        "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,  # group E, not in payload
                        "saml_id": "saml_id1",  # group E
                        "default_password": "def_password",  # group F, will be cleared
                        "is_demo_user": True,  # group G
                    }
                ],
            },
        )

        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.NEW
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Following groups were not found: 'group4'",
        ]
        assert row["data"] == {
            "username": {"value": "user2", "info": "done"},
            "first_name": {"value": "Jim", "info": "done"},
            "vote_weight": {"value": "1.234560", "info": "done"},
            "saml_id": {"value": "saml_id1", "info": "new"},
            "default_password": {"value": "", "info": "warning"},
            "groups": [
                {"value": "group1", "info": "done", "id": 1},
                {"value": "group2", "info": "done", "id": 2},
                {"value": "group3", "info": "done", "id": 3},
                {"value": "group4", "info": "warning"},
            ],
        }
