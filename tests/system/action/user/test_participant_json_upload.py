from time import time

from openslides_backend.action.mixins.import_mixins import ImportState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.patterns import fqid_from_collection_and_id
from tests.system.action.base import BaseActionTestCase


class ParticipantJsonUpload(BaseActionTestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        super().setUp()
        self.set_models(
            {
                "organization/1": {"gender_ids": [1, 2, 3, 4]},
                "gender/1": {"name": "male"},
                "gender/2": {"name": "female"},
                "gender/3": {"name": "diverse"},
                "gender/4": {"name": "non-binary"},
                "meeting/1": {
                    "name": "test",
                    "group_ids": [1, 7],
                    "structure_level_ids": [1],
                    "admin_group_id": 7,
                },
                "group/1": {"name": "testgroup", "meeting_id": 1},
                "group/7": {
                    "name": "custom_admin_group",
                    "meeting_id": 1,
                    "admin_group_for_meeting_id": 1,
                },
                "structure_level/1": {"name": "testlevel", "meeting_id": 1},
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
                        "structure_level": ["testlevel", "notfound"],
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
            "messages": [],
            "data": {
                "username": {"value": "test", "info": ImportState.DONE},
                "default_password": {"value": "secret", "info": ImportState.DONE},
                "is_active": {"value": True, "info": ImportState.DONE},
                "is_physical_person": {"value": False, "info": ImportState.DONE},
                "number": {"value": "strange number", "info": ImportState.DONE},
                "structure_level": [
                    {"value": "testlevel", "info": ImportState.DONE, "id": 1},
                    {"value": "notfound", "info": ImportState.NEW},
                ],
                "vote_weight": {"value": "1.120000", "info": ImportState.DONE},
                "comment": {"value": "my comment", "info": ImportState.DONE},
                "is_present": {"value": False, "info": ImportState.DONE},
                "groups": [
                    {"value": "testgroup", "info": ImportState.DONE, "id": 1},
                    {"value": "notfound_group1", "info": ImportState.NEW},
                    {"value": "notfound_group2", "info": ImportState.NEW},
                ],
            },
        }
        assert {"name": "groups created", "value": 2} in response.json["results"][0][0][
            "statistics"
        ]
        import_preview_id = response.json["results"][0][0].get("id")
        import_preview_fqid = fqid_from_collection_and_id(
            "import_preview", import_preview_id
        )
        import_preview = self.assert_model_exists(
            import_preview_fqid, {"name": "participant", "state": ImportState.DONE}
        )
        assert start_time <= import_preview["created"] <= end_time

    def test_json_upload_remove_last_admin(self) -> None:
        self.create_user("bob", [7])
        self.set_models({"group/1": {"default_group_for_meeting_id": 1}})
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "bob",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.ERROR,
            "messages": ["Error: Cannot remove last member of admin group"],
            "data": {
                "id": 2,
                "username": {"id": 2, "value": "bob", "info": ImportState.DONE},
                "groups": [
                    {"value": "testgroup", "info": ImportState.GENERATED, "id": 1},
                    {"value": "", "info": ImportState.ERROR},
                ],
            },
        }

    def test_json_upload_remove_last_admins(self) -> None:
        self.create_user("bob", [7])
        self.create_user("alice", [7])
        self.set_models({"group/1": {"default_group_for_meeting_id": 1}})
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "bob",
                    },
                    {
                        "username": "alice",
                    },
                ],
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.ERROR,
            "messages": ["Error: Cannot remove last member of admin group"],
            "data": {
                "id": 2,
                "username": {"id": 2, "value": "bob", "info": ImportState.DONE},
                "groups": [
                    {"value": "testgroup", "info": ImportState.GENERATED, "id": 1},
                    {"value": "", "info": ImportState.ERROR},
                ],
            },
        }
        assert response.json["results"][0][0]["rows"][1] == {
            "state": ImportState.ERROR,
            "messages": ["Error: Cannot remove last member of admin group"],
            "data": {
                "id": 3,
                "username": {"id": 3, "value": "alice", "info": ImportState.DONE},
                "groups": [
                    {"value": "testgroup", "info": ImportState.GENERATED, "id": 1},
                    {"value": "", "info": ImportState.ERROR},
                ],
            },
        }

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
            "Import tries to use non-existent meeting 111" in response.json["message"]
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
                {"property": "member_number", "type": "string", "is_object": True},
                {
                    "property": "structure_level",
                    "type": "string",
                    "is_object": True,
                    "is_list": True,
                },
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
                {"property": "locked_out", "type": "boolean", "is_object": True},
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
                {"name": "structure levels created", "value": 0},
                {"name": "groups created", "value": 0},
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

    def test_json_upload_permission_2(self) -> None:
        self.base_permission_test(
            {},
            "participant.json_upload",
            {"meeting_id": 1, "data": [{"username": "test"}]},
            Permissions.User.CAN_UPDATE,
            True,
        )

    def test_json_upload_no_permission_meeting_admin(self) -> None:
        self.create_meeting()
        self.create_meeting(4)
        user_id = self.create_user_for_meeting(1)
        self.set_models(
            {
                f"user/3": self._get_user_data("test", {1: [], 4: []}),
            }
        )
        self.set_user_groups(user_id, [2])
        meetingusers = self.set_user_groups(3, [1, 4])
        self.login(user_id)
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {"username": "test", "gender": "male", "default_password": "secret"}
                ],
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
                            "state": ImportState.DONE,
                            "messages": ['Following fields were removed from payload, because the user has no permissions to change them: username, gender_id, default_password'],
                            "data": {
                                "username": {
                                    "value": "test",
                                    "info": ImportState.REMOVE,
                                    "id": 3,
                                },
                                "default_password": {
                                    "value": "secret",
                                    "info": ImportState.REMOVE,
                                },
                                "id":3,
                                "groups": [
                                    {
                                        "info": ImportState.GENERATED,
                                        "value": "group1",
                                        "id": 1,
                                    }
                                ],
                                "gender": {
                                    "info": ImportState.REMOVE,
                                    "value": "male",
                                    "id": 1,
                                },
                            },
                        }
                    ],
                },
            },
        )

    def test_json_upload_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "participant.json_upload",
            {"meeting_id": 1, "data": [{"username": "test"}]},
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
                "gender/1": {"name": "male"},
            }
        )
        fix_fields = {
            "first_name": "Max",
            "last_name": "Mustermann",
            "email": "test@ntvtn.de",
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
                        "structure_level": "testlevel",
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
        assert row["data"]["gender"] == {"id": 1, "value": "male", "info": "done"}
        assert row["data"]["groups"] == [
            {"value": "testgroup", "info": "generated", "id": 1}
        ]
        assert row["data"]["structure_level"] == [
            {"value": "testlevel", "info": "done", "id": 1}
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
            "gender": "notAGender",
        }
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "vote_weight": "1.456",
                        "is_present": "0",
                        "structure_level": "testlevel",
                        **fix_fields,
                    }
                ],
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
        assert entry["data"]["structure_level"] == [
            {
                "value": "testlevel",
                "info": ImportState.DONE,
                "id": 1,
            }
        ]
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

    def test_json_upload_not_sufficient_field_permission_update_with_wrong_email(
        self,
    ) -> None:
        self.create_meeting(1)
        self.create_meeting(4)
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
                        "username": "user2",
                        "email": "Jim.Knopf@@Lummer.land",
                        "vote_weight": "1.23456",
                    }
                ],
            },
        )

        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Error: 'Jim.Knopf@@Lummer.land' is not a valid email address.",
            "Following fields were removed from payload, because the user has no permissions to change them: username, email",
        ]
        assert row["data"] == {
            "id": 2,
            "username": {"value": "user2", "info": "remove", "id": 2},
            "email": {"value": "Jim.Knopf@@Lummer.land", "info": ImportState.ERROR},
            "vote_weight": {"value": "1.234560", "info": "done"},
            "groups": [{"id": 1, "info": ImportState.GENERATED, "value": "group1"}],
        }

    def test_json_upload_wrong_email(self) -> None:
        self.create_meeting(1)
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
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
        assert import_preview["name"] == "participant"
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

    def test_json_upload_with_illegal_decimal_value(self) -> None:
        self.create_meeting(1)
        self.create_user("test user", [3])
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "test user",
                        "first_name": "test",
                        "groups": ["group3"],
                        "vote_weight": "2/3",
                    },
                ],
            },
        )
        self.assert_status_code(response, 400)
        assert "Could not parse 2/3 expect decimal" in response.json["message"]

    def test_json_upload_update_member_number_in_existing_participant_error(
        self,
    ) -> None:
        self.create_meeting(1)
        self.create_user("test", [3])
        self.set_models(
            {
                "user/2": {
                    "default_vote_weight": "2.300000",
                    "member_number": "old_one",
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
                        "member_number": "new_one",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Member numbers can't be updated via import"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "member_number": {"info": ImportState.ERROR, "value": "new_one"},
            "username": {"info": "done", "value": "test", "id": 2},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

    def test_json_upload_update_duplicate_member_numbers(self) -> None:
        self.create_meeting(1)
        self.create_user("test1", [3])
        self.set_models(
            {
                "user/2": {
                    "default_vote_weight": "2.300000",
                },
            }
        )
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
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
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Found more users with the same member number"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "member_number": {"info": ImportState.ERROR, "value": "new_one"},
            "username": {"info": "done", "value": "test1", "id": 2},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }
        assert import_preview["result"]["rows"][1]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][1]["messages"] == [
            "Error: Found more users with the same member number"
        ]
        data = import_preview["result"]["rows"][1]["data"]
        assert data == {
            "member_number": {"info": ImportState.ERROR, "value": "new_one"},
            "username": {"info": "done", "value": "test2"},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

    def test_json_upload_set_other_persons_member_number_in_existing_participant(
        self,
    ) -> None:
        self.create_meeting(1)
        self.create_user("test", [3])
        self.create_user("test2", [3])
        self.set_models(
            {
                "user/2": {
                    "default_vote_weight": "2.300000",
                },
                "user/3": {
                    "member_number": "new_one",
                    "default_vote_weight": "2.300000",
                },
            }
        )
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
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
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Member number doesn't match detected user"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "member_number": {"info": ImportState.ERROR, "value": "new_one"},
            "username": {"info": "done", "value": "test", "id": 2},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

    def test_json_upload_set_other_persons_member_number_in_existing_participant_2(
        self,
    ) -> None:
        self.create_meeting(1)
        self.create_user("test", [3])
        self.create_user("test2", [3])
        self.set_models(
            {
                "user/2": {"default_vote_weight": "2.300000", "saml_id": "tessst"},
                "user/3": {
                    "member_number": "new_one",
                    "default_vote_weight": "2.300000",
                },
            }
        )
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
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
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert sorted(import_preview["result"]["rows"][0]["messages"]) == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Error: Member number doesn't match detected user",
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "default_password": {
                "info": "warning",
                "value": "",
            },
            "member_number": {"info": ImportState.ERROR, "value": "new_one"},
            "username": {"info": "done", "value": "test", "id": 2},
            "saml_id": {"info": "done", "value": "tessst"},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

    def test_json_upload_set_other_persons_member_number_in_existing_participant_3(
        self,
    ) -> None:
        self.create_meeting(1)
        self.create_user("test", [3])
        self.create_user("test2", [3])
        self.set_models(
            {
                "user/2": {
                    "default_vote_weight": "2.300000",
                    "first_name": "Fritz",
                    "last_name": "Chen",
                    "email": "fritz.chen@scho.ol",
                },
                "user/3": {
                    "member_number": "new_one",
                    "default_vote_weight": "2.300000",
                },
            }
        )
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
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
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Member number doesn't match detected user"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "member_number": {"info": ImportState.ERROR, "value": "new_one"},
            "username": {"info": "done", "value": "test", "id": 2},
            "first_name": {"info": "done", "value": "Fritz"},
            "last_name": {"info": "done", "value": "Chen"},
            "email": {"info": "done", "value": "fritz.chen@scho.ol"},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

    def prepare_locked_out_test(
        self,
        username: str = "",
        group_ids: list[int] = [],
        oml: OrganizationManagementLevel | None = None,
    ) -> None:
        self.create_meeting()
        self.create_meeting(5)
        self.set_models(
            {
                "meeting/1": {"group_ids": [1, 2, 3, 4]},
                "group/1": {"meeting_id": 1, "name": "default"},
                "group/2": {"meeting_id": 1, "name": "admin"},
                "group/3": {"meeting_id": 1, "name": "can_manage"},
                "group/4": {"meeting_id": 1, "name": "can_update"},
            }
        )
        self.add_group_permissions(3, [Permissions.User.CAN_MANAGE])
        self.add_group_permissions(4, [Permissions.User.CAN_UPDATE])
        self.add_group_permissions(7, [Permissions.User.CAN_MANAGE])
        if username:
            self.create_user(username, group_ids, oml)

    def test_json_upload_create_locked_out_user_meeting_admin_error(self) -> None:
        self.prepare_locked_out_test()
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [{"username": "test", "locked_out": "1", "groups": ["admin"]}],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Group(s) 2 have user.can_manage permissions and may therefore not be used by users who are locked out"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        for key, value in {
            "username": {"info": "done", "value": "test"},
            "locked_out": {"info": "error", "value": True},
            "groups": [{"id": 2, "info": "error", "value": "admin"}],
        }.items():
            assert data[key] == value

    def test_json_upload_create_locked_out_user_can_manage_error(self) -> None:
        self.prepare_locked_out_test()
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {"username": "test", "locked_out": "1", "groups": ["can_manage"]}
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Group(s) 3 have user.can_manage permissions and may therefore not be used by users who are locked out"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        for key, value in {
            "username": {"info": "done", "value": "test"},
            "locked_out": {"info": "error", "value": True},
            "groups": [{"id": 3, "info": "error", "value": "can_manage"}],
        }.items():
            assert data[key] == value

    def test_json_upload_update_locked_out_on_self_error(self) -> None:
        self.prepare_locked_out_test()
        self.set_user_groups(1, [3])
        self.set_models(
            {"user/1": {"username": "admin", "organization_management_level": None}}
        )
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "admin",
                        "locked_out": "1",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: You may not lock yourself out of a meeting"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        for key, value in {
            "username": {"info": "done", "value": "admin", "id": 1},
            "locked_out": {"info": "error", "value": True},
            "groups": [{"id": 1, "info": "generated", "value": "default"}],
        }.items():
            assert data[key] == value

    def test_json_upload_update_locked_out_meeting_admin_error(self) -> None:
        self.prepare_locked_out_test("test", [1])
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [{"username": "test", "locked_out": "1", "groups": ["admin"]}],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Group(s) 2 have user.can_manage permissions and may therefore not be used by users who are locked out"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        for key, value in {
            "id": 2,
            "username": {"info": "done", "value": "test", "id": 2},
            "locked_out": {"info": "error", "value": True},
            "groups": [{"id": 2, "info": "error", "value": "admin"}],
        }.items():
            assert data[key] == value

    def test_json_upload_update_locked_out_on_superadmin_error(self) -> None:
        self.prepare_locked_out_test("test", oml=OrganizationManagementLevel.SUPERADMIN)
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "test",
                        "locked_out": "1",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Cannot lock user from meeting 1 as long as he has the OrganizationManagementLevel superadmin"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        for key, value in {
            "id": 2,
            "username": {"info": "done", "value": "test", "id": 2},
            "locked_out": {"info": "error", "value": True},
            "groups": [{"id": 1, "info": "generated", "value": "default"}],
        }.items():
            assert data[key] == value

    def test_json_upload_update_locked_out_on_other_oml_error(self) -> None:
        self.prepare_locked_out_test(
            "test", oml=OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "test",
                        "locked_out": "1",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Cannot lock user from meeting 1 as long as he has the OrganizationManagementLevel can_manage_users"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        for key, value in {
            "id": 2,
            "username": {"info": "done", "value": "test", "id": 2},
            "locked_out": {"info": "error", "value": True},
            "groups": [{"id": 1, "info": "generated", "value": "default"}],
        }.items():
            assert data[key] == value

    def test_json_upload_update_locked_out_on_cml_error(self) -> None:
        self.prepare_locked_out_test("test", [1])
        self.set_models(
            {
                "user/2": {"committee_management_ids": [60]},
                "committee/60": {"manager_ids": [2]},
            }
        )
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "test",
                        "locked_out": "1",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Cannot lock user out of meeting 1 as he is manager of the meetings committee"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        for key, value in {
            "id": 2,
            "username": {"info": "done", "value": "test", "id": 2},
            "locked_out": {"info": "error", "value": True},
            "groups": [{"id": 1, "info": "generated", "value": "default"}],
        }.items():
            assert data[key] == value

    def test_json_upload_update_meeting_admin_on_locked_out_user_error(self) -> None:
        self.prepare_locked_out_test("test", [1])
        self.set_models({"meeting_user/1": {"locked_out": True}})
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [{"username": "test", "groups": ["admin"]}],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.ERROR
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.ERROR
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Error: Group(s) 2 have user.can_manage permissions and may therefore not be used by users who are locked out"
        ]
        data = import_preview["result"]["rows"][0]["data"]
        for key, value in {
            "username": {"info": "done", "value": "test", "id": 2},
            "groups": [{"info": "error", "value": "admin", "id": 2}],
        }.items():
            assert data[key] == value

    def test_json_upload_permission_as_locked_out(self) -> None:
        self.create_meeting()
        self.set_group_permissions(3, [Permissions.User.CAN_MANAGE])
        meeting_user_id = self.set_user_groups(1, [3])[0]
        self.set_models(
            {
                f"meeting_user/{meeting_user_id}": {"locked_out": True},
                "user/1": {"organization_management_level": None},
            }
        )
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
                        "structure_level": ["testlevel", "notfound"],
                        "vote_weight": "1.12",
                        "comment": "my comment",
                        "is_present": "0",
                        "groups": ["testgroup", "notfound_group1", "notfound_group2"],
                        "wrong": 15,
                    }
                ],
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action participant.json_upload. Missing permissions: Permission user.can_manage in meeting 1 or OrganizationManagementLevel can_manage_organization in organization 1 or CommitteeManagementLevel can_manage in committee 60",
            response.json["message"],
        )


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
                },
                **{
                    f"group/{id_}": {"permissions": ["assignment.can_see"]}
                    for id_ in range(1, 7)
                },
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

        assert import_preview["result"]["rows"][1]["messages"] == []
        assert import_preview["result"]["rows"][1]["data"]["username"] == {
            "info": "done",
            "value": "test_saml_id1",
        }
        assert import_preview["result"]["rows"][1]["data"]["groups"] == [
            {"value": "group1", "info": ImportState.DONE, "id": 1},
            {"value": "group2", "info": ImportState.DONE, "id": 2},
            {"value": "group3", "info": ImportState.DONE, "id": 3},
            {"value": "group4", "info": ImportState.NEW},
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
                    "structure_level_ids": [1, 2],
                },
                "structure_level/1": {
                    "meeting_id": 1,
                    "name": "old sl",
                },
                "structure_level/2": {
                    "meeting_id": 1,
                    "name": "new sl",
                },
                "meeting_user/110": {
                    "meeting_id": 1,
                    "user_id": 10,
                    "structure_level_ids": [1],
                    "number": "old number",
                    "comment": "old comment",
                },
            }
        )
        fix_fields = {
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
                        "structure_level": "new sl",
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
            "structure_level": [{"id": 2, "info": "done", "value": "new sl"}],
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
                "organization/1": {"gender_ids": [1, 2, 3, 4]},
                "gender/1": {"name": "male"},
                "gender/2": {"name": "female"},
                "gender/3": {"name": "diverse"},
                "gender/4": {"name": "non-binary"},
                "user/2": {
                    "username": "user2",
                    "password": "secret",
                    "default_password": "secret",
                    "can_change_own_password": True,
                    "default_vote_weight": "2.300000",
                    "gender_id": 1,
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
                "group/8": {
                    "meeting_id": 1,
                    "name": "Anonymous",
                    "anonymous_group_for_meeting_id": 1,
                },
                "meeting/1": {
                    "meeting_user_ids": [31],
                    "group_ids": [1, 2, 3, 7, 8],
                    "anonymous_group_id": 8,
                },
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
                        "structure_level": ["level up"],
                        "gender": "diverse",
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
                        "structure_level": ["level up", "no. 5"],
                        "gender": "unknown",
                    },
                    {"saml_id": "new_saml6", "groups": ["group4"], "is_present": "1"},
                    {
                        "first_name": "Joan",
                        "last_name": "Baez7",
                        "groups": [
                            "group2",
                            "group4",
                            "Anonymous",
                            "unknown",
                            "group7M1",
                        ],
                        "gender": "female",
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
        ]
        assert import_preview["result"]["rows"][0]["data"] == {
            "id": 2,
            "saml_id": {"info": "new", "value": "test_saml_id2"},
            "username": {"id": 2, "info": "done", "value": "user2"},
            "default_password": {"info": "warning", "value": ""},
            "groups": [
                {"id": 3, "info": "done", "value": "group3"},
                {"info": "new", "value": "group4"},
            ],
            "structure_level": [{"value": "level up", "info": ImportState.NEW}],
            "gender": {"id": 3, "info": ImportState.DONE, "value": "diverse"},
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
        assert import_preview["result"]["rows"][2]["messages"] == []
        assert import_preview["result"]["rows"][2]["data"] == {
            "id": 4,
            "email": {"value": "mlk@america.com", "info": ImportState.DONE},
            "username": {"id": 4, "info": "done", "value": "user4"},
            "last_name": {"value": "Luther King", "info": ImportState.DONE},
            "first_name": {"value": "Martin", "info": ImportState.DONE},
            "groups": [
                {"info": "new", "value": "group4"},
            ],
        }

        assert import_preview["result"]["rows"][3]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][3]["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Gender 'unknown' is not in the allowed gender list.",
        ]
        assert import_preview["result"]["rows"][3]["data"] == {
            "saml_id": {"info": "new", "value": "saml5"},
            "username": {"info": "done", "value": "new_user5"},
            "default_password": {"info": "warning", "value": ""},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
            "structure_level": [
                {"value": "level up", "info": ImportState.NEW},
                {"value": "no. 5", "info": ImportState.NEW},
            ],
            "gender": {"info": ImportState.WARNING, "value": "unknown"},
        }

        assert import_preview["result"]["rows"][4]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][4]["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides."
        ]
        assert import_preview["result"]["rows"][4]["data"] == {
            "saml_id": {"info": "new", "value": "new_saml6"},
            "username": {"info": "generated", "value": "new_saml6"},
            "default_password": {"info": "warning", "value": ""},
            "is_present": {"info": "done", "value": True},
            "groups": [
                {"info": "new", "value": "group4"},
            ],
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
            "groups": [
                {"id": 2, "info": "done", "value": "group2"},
                {"info": "new", "value": "group4"},
                {"info": "new", "value": "Anonymous"},
                {"info": "new", "value": "unknown"},
                {"id": 7, "info": "done", "value": "group7M1"},
            ],
            "gender": {"id": 2, "info": ImportState.DONE, "value": "female"},
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
                        "email": "Jim.Knopf@Lummer.land",  # group A, will be removed
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
            "Following fields were removed from payload, because the user has no permissions to change them: username, first_name, email, saml_id, default_password",
        ]
        assert row["data"] == {
            "id": 2,
            "username": {"value": "user2", "info": "remove", "id": 2},
            "first_name": {"value": "Jim", "info": "remove"},
            "email": {"value": "Jim.Knopf@Lummer.land", "info": "remove"},
            "vote_weight": {"value": "1.234560", "info": "done"},
            "saml_id": {"value": "saml_id1", "info": "remove"},
            "default_password": {"value": "", "info": "remove"},
            "groups": [
                {"value": "group1", "info": "done", "id": 1},
                {"value": "group2", "info": "done", "id": 2},
                {"value": "group3", "info": "done", "id": 3},
                {"value": "group4", "info": "new"},
            ],
        }

    def json_upload_not_sufficient_field_permission_update_with_member_number(
        self,
    ) -> None:
        """try to change users first_name, but missing rights for user_scope committee"""
        self.set_models(
            {
                "user/1": {"organization_management_level": None},
                "user/2": {
                    "username": "user2",
                    "member_number": "M3MNUM",
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
                        "member_number": "M3MNUM",  # group A, will be removed
                        "first_name": "Jim",  # group A, will be removed
                        "email": "Jim.Knopf@Lummer.land",  # group A, will be removed
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
            "Following fields were removed from payload, because the user has no permissions to change them: member_number, first_name, email, username, saml_id, default_password",
        ]
        assert row["data"] == {
            "id": 2,
            "username": {"value": "user2", "info": "remove"},
            "member_number": {"value": "M3MNUM", "info": "remove", "id": 2},
            "first_name": {"value": "Jim", "info": "remove"},
            "email": {"value": "Jim.Knopf@Lummer.land", "info": "remove"},
            "vote_weight": {"value": "1.234560", "info": "done"},
            "saml_id": {"value": "saml_id1", "info": "remove"},
            "default_password": {"value": "", "info": "remove"},
            "groups": [
                {"value": "group1", "info": "done", "id": 1},
                {"value": "group2", "info": "done", "id": 2},
                {"value": "group3", "info": "done", "id": 3},
                {"value": "group4", "info": "new"},
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
                {"value": "group4", "info": "new"},
            ],
        }

    def json_upload_legacy_username(self) -> None:
        self.create_meeting(1)
        user_id = self.create_user("test user", [3])
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "test user",
                        "first_name": "test",
                        "groups": ["group3"],
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
                "id": user_id,
                "username": {
                    "id": user_id,
                    "info": ImportState.DONE,
                    "value": "test user",
                },
                "first_name": {"info": ImportState.DONE, "value": "test"},
                "groups": [
                    {
                        "id": 3,
                        "info": "done",
                        "value": "group3",
                    },
                ],
            },
        }

    def json_upload_update_reference_via_two_attributes(self) -> None:
        self.create_meeting(1)
        self.create_user("test", [3])
        self.set_models(
            {
                "user/2": {
                    "default_vote_weight": "2.300000",
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
                        "saml_id": "old_one",
                        "default_vote_weight": "4.500000",
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
            "saml_id": {"info": "done", "value": "old_one"},
            "username": {"info": "done", "value": "test", "id": 2},
            "default_vote_weight": {"info": "done", "value": "4.500000"},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

    def json_upload_set_member_number_in_existing_participants(self) -> None:
        self.create_meeting(1)
        self.create_user("test1", [3])
        self.create_user("test2", [3])
        self.create_user("test3", [3])
        self.set_models(
            {
                "user/2": {
                    "default_vote_weight": "2.300000",
                },
                "user/3": {"saml_id": "samLidman"},
                "user/4": {
                    "first_name": "Hasan",
                    "last_name": "Ame",
                    "email": "hasaN.ame@nd.email",
                },
            }
        )
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
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
        assert import_preview["state"] == ImportState.WARNING
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == []
        row = import_preview["result"]["rows"][0]["data"]
        assert row == {
            "id": 2,
            "username": {"info": "done", "value": "test1", "id": 2},
            "member_number": {"info": "new", "value": "new_one"},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }
        row = import_preview["result"]["rows"][1]["data"]
        assert row == {
            "id": 3,
            "username": {"info": "done", "value": "test2", "id": 3},
            "saml_id": {"info": "done", "value": "samLidman"},
            "default_password": {"info": "warning", "value": ""},
            "member_number": {"info": "new", "value": "another_new_1"},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }
        row = import_preview["result"]["rows"][2]["data"]
        assert row == {
            "id": 4,
            "username": {"info": "done", "value": "test3", "id": 4},
            "first_name": {"info": "done", "value": "Hasan"},
            "last_name": {"info": "done", "value": "Ame"},
            "email": {"info": "done", "value": "hasaN.ame@nd.email"},
            "member_number": {"info": "new", "value": "UGuessedIt"},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

    def json_upload_set_other_matching_criteria_in_existing_participant_via_member_number(
        self,
    ) -> None:
        self.create_meeting(1)
        self.create_user("test", [3])
        self.set_models(
            {
                "user/2": {
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
            "participant.json_upload",
            {
                "meeting_id": 1,
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
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.DONE
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides."
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "id": 2,
            "default_password": {"value": "", "info": "warning"},
            "username": {"info": "new", "value": "newname"},
            "saml_id": {"info": "new", "value": "some_other_saml"},
            "first_name": {"info": "done", "value": "second"},
            "last_name": {"info": "done", "value": "second_to_last"},
            "member_number": {"info": "done", "value": "M3MNUM", "id": 2},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

    def json_upload_add_member_number(self) -> None:
        self.create_meeting(1)
        self.create_user("test", [3])
        self.set_models(
            {
                "user/2": {
                    "default_vote_weight": "2.300000",
                    "member_number": "old_one",
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
                        "member_number": "old_one",
                        "vote_weight": "4.345678",
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
            "member_number": {"info": "done", "value": "old_one", "id": 2},
            "username": {"info": "done", "value": "test"},
            "vote_weight": {"info": "done", "value": "4.345678"},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

    def json_upload_new_participant_with_member_number(self) -> None:
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
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
        assert import_preview["name"] == "participant"
        assert import_preview["result"]["rows"][0]["state"] == ImportState.NEW
        assert import_preview["result"]["rows"][0]["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides."
        ]
        data = import_preview["result"]["rows"][0]["data"]
        assert data == {
            "default_password": {"value": "", "info": "warning"},
            "username": {"info": "done", "value": "newname"},
            "saml_id": {"info": "new", "value": "some_other_saml"},
            "first_name": {"info": "done", "value": "second"},
            "last_name": {"info": "done", "value": "second_to_last"},
            "member_number": {"info": "done", "value": "M3MNUM"},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

    def json_upload_dont_recognize_empty_name_and_email(self) -> None:
        self.set_models(
            {
                "organization/1": {
                    "user_ids": [1, 3, 4, 5],
                    "saml_enabled": False,
                    "committee_ids": [1],
                    "active_meeting_ids": [1],
                },
                "committee/1": {
                    "name": "jk",
                    "meeting_ids": [1],
                    "organization_id": 1,
                },
                "meeting/1": {
                    "name": "jk",
                    "group_ids": [1, 2],
                    "committee_id": 1,
                    "admin_group_id": 2,
                    "default_group_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "group/1": {
                    "name": "Default",
                    "meeting_id": 1,
                    "default_group_for_meeting_id": 1,
                },
                "group/2": {
                    "name": "Admin",
                    "meeting_id": 1,
                    "admin_group_for_meeting_id": 1,
                },
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
            "participant.json_upload",
            {
                "data": [
                    {
                        "member_number": "mem_nr",
                    }
                ],
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE

    def json_upload_remove_last_admin_add_a_new_one(self) -> None:
        self.create_user("bob", [2])
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "bob",
                    },
                    {"username": "alice", "groups": ["group2"]},
                ],
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.DONE,
            "messages": [],
            "data": {
                "id": 2,
                "username": {"id": 2, "value": "bob", "info": ImportState.DONE},
                "groups": [
                    {"value": "group1", "info": ImportState.GENERATED, "id": 1},
                ],
            },
        }
        row = response.json["results"][0][0]["rows"][1]
        assert row["state"] == ImportState.NEW
        assert row["messages"] == []
        assert row["data"]["username"] == {"value": "alice", "info": ImportState.DONE}
        assert row["data"]["groups"] == [
            {"value": "group2", "info": ImportState.DONE, "id": 2}
        ]

    def json_upload_remove_admin_group_normal(self) -> None:
        self.create_user("bob", [2])
        self.create_user("alice", [2])
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "bob",
                    },
                ],
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.DONE,
            "messages": [],
            "data": {
                "id": 2,
                "username": {"id": 2, "value": "bob", "info": ImportState.DONE},
                "groups": [
                    {"value": "group1", "info": ImportState.GENERATED, "id": 1},
                ],
            },
        }

    def json_upload_remove_last_admin_in_template(self) -> None:
        self.create_user("bob", [2])
        self.set_models(
            {
                "group/1": {"default_group_for_meeting_id": 1},
                "meeting/1": {"template_for_organization_id": 1},
                "organization/1": {"template_meeting_ids": [1]},
            }
        )
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "bob",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.DONE,
            "messages": [],
            "data": {
                "id": 2,
                "username": {"id": 2, "value": "bob", "info": ImportState.DONE},
                "groups": [
                    {"value": "group1", "info": ImportState.GENERATED, "id": 1},
                ],
            },
        }

    def json_upload_multi_with_locked_out(self) -> None:
        self.create_meeting()
        self.create_meeting(5)
        self.set_models(
            {
                "meeting/1": {"group_ids": [1, 2, 3, 4]},
                "group/1": {"meeting_id": 1, "name": "default"},
                "group/2": {"meeting_id": 1, "name": "admin"},
                "group/3": {"meeting_id": 1, "name": "can_manage"},
                "group/4": {"meeting_id": 1, "name": "can_update"},
            }
        )
        self.add_group_permissions(3, [Permissions.User.CAN_MANAGE])
        self.add_group_permissions(4, [Permissions.User.CAN_UPDATE])
        self.add_group_permissions(7, [Permissions.User.CAN_MANAGE])
        participant1 = self.create_user("participant1", [1])  # 1
        foreign_cml = self.create_user("foreign_cml")
        can_update = self.create_user("can_update", [4])  # 2
        foreign_meeting_admin = self.create_user("foreign_meeting_admin", [6])  # 3
        foreign_can_manage = self.create_user("foreign_can_manage", [7])  # 4
        can_manage = self.create_user("can_manage", [3])  # 5
        meeting_admin = self.create_user("meeting_admin", [2])  # 6
        locked_out1 = self.create_user("locked_out1", [1])  # 7
        locked_out2 = self.create_user("locked_out2", [1])  # 8
        self.set_models(
            {
                f"committee/{64}": {"manager_ids": [foreign_cml]},
                f"user/{foreign_cml}": {"committee_management_ids": [64]},
                "meeting_user/7": {"locked_out": True},
                "meeting_user/8": {"locked_out": True},
            }
        )
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "new_can_update",
                        "groups": ["can_update"],
                        "locked_out": "1",
                    },
                    {
                        "username": "new_default",
                        "groups": ["default"],
                        "locked_out": "1",
                    },
                    {
                        "username": "participant1",
                        "groups": ["can_update"],
                        "locked_out": "1",
                    },
                    {
                        "username": "foreign_cml",
                        "locked_out": "1",
                    },
                    {
                        "username": "can_update",
                        "locked_out": "1",
                    },
                    {
                        "username": "foreign_meeting_admin",
                        "locked_out": "1",
                    },
                    {
                        "username": "foreign_can_manage",
                        "locked_out": "1",
                    },
                    {
                        "username": "can_manage",
                        "locked_out": "1",
                        "groups": ["default"],
                    },
                    {
                        "username": "meeting_admin",
                        "locked_out": "1",
                        "groups": ["default"],
                    },
                    {"username": "locked_out1", "locked_out": "0", "groups": ["admin"]},
                    {
                        "username": "locked_out2",
                        "locked_out": "0",
                        "groups": ["can_manage"],
                    },
                ],
            },
        )
        self.assert_status_code(response, 200)
        import_preview = self.assert_model_exists("import_preview/1")
        assert import_preview["state"] == ImportState.DONE
        assert import_preview["name"] == "participant"
        rows = import_preview["result"]["rows"]
        assert not any(len(row["messages"]) for row in rows)
        assert not any(row["state"] != ImportState.NEW for row in rows[:2])
        assert not any(row["state"] != ImportState.DONE for row in rows[2:])
        data = [row["data"] for row in rows]
        assert not any(
            date["locked_out"] != {"info": "done", "value": True} for date in data[0:9]
        )
        assert not any(data[i + 2]["id"] != participant1 + i for i in range(9))
        i = 0
        assert data[i]["username"] == {
            "info": "done",
            "value": "new_can_update",
        }
        assert data[i]["groups"] == [
            {
                "id": 4,
                "info": "done",
                "value": "can_update",
            },
        ]
        i += 1
        assert data[i]["username"] == {
            "info": "done",
            "value": "new_default",
        }
        assert data[i]["groups"] == [
            {
                "id": 1,
                "info": "done",
                "value": "default",
            },
        ]
        i += 1
        assert data[i]["username"] == {
            "id": participant1,
            "info": "done",
            "value": "participant1",
        }
        assert data[i]["groups"] == [
            {
                "id": 4,
                "info": "done",
                "value": "can_update",
            },
        ]
        i += 1
        assert data[i]["username"] == {
            "id": foreign_cml,
            "info": "done",
            "value": "foreign_cml",
        }
        assert data[i]["groups"] == [
            {
                "id": 1,
                "info": "generated",
                "value": "default",
            },
        ]
        i += 1
        assert data[i]["username"] == {
            "id": can_update,
            "info": "done",
            "value": "can_update",
        }
        assert data[i]["groups"] == [
            {
                "id": 1,
                "info": "generated",
                "value": "default",
            },
        ]
        i += 1
        assert data[i]["username"] == {
            "id": foreign_meeting_admin,
            "info": "done",
            "value": "foreign_meeting_admin",
        }
        assert data[i]["groups"] == [
            {
                "id": 1,
                "info": "generated",
                "value": "default",
            },
        ]
        i += 1
        assert data[i]["username"] == {
            "id": foreign_can_manage,
            "info": "done",
            "value": "foreign_can_manage",
        }
        assert data[i]["groups"] == [
            {
                "id": 1,
                "info": "generated",
                "value": "default",
            },
        ]
        i += 1
        assert data[i]["username"] == {
            "id": can_manage,
            "info": "done",
            "value": "can_manage",
        }
        assert data[i]["groups"] == [
            {
                "id": 1,
                "info": "done",
                "value": "default",
            },
        ]
        i += 1
        assert data[i]["username"] == {
            "id": meeting_admin,
            "info": "done",
            "value": "meeting_admin",
        }
        assert data[i]["groups"] == [
            {
                "id": 1,
                "info": "done",
                "value": "default",
            },
        ]
        i += 1
        assert data[i]["username"] == {
            "id": locked_out1,
            "info": "done",
            "value": "locked_out1",
        }
        assert data[i]["groups"] == [
            {
                "id": 2,
                "info": "done",
                "value": "admin",
            },
        ]
        i += 1
        assert data[i]["username"] == {
            "id": locked_out2,
            "info": "done",
            "value": "locked_out2",
        }
        assert data[i]["groups"] == [
            {
                "id": 3,
                "info": "done",
                "value": "can_manage",
            },
        ]

    def json_upload_update_locked_out_on_meeting_admin_auto_overwrite_group(
        self,
    ) -> None:
        self.create_meeting()
        self.create_meeting(5)
        self.set_models(
            {
                "meeting/1": {"group_ids": [1, 2, 3, 4]},
                "group/1": {"meeting_id": 1, "name": "default"},
                "group/2": {"meeting_id": 1, "name": "admin"},
                "group/3": {"meeting_id": 1, "name": "can_manage"},
                "group/4": {"meeting_id": 1, "name": "can_update"},
            }
        )
        self.add_group_permissions(3, [Permissions.User.CAN_MANAGE])
        self.add_group_permissions(4, [Permissions.User.CAN_UPDATE])
        self.add_group_permissions(7, [Permissions.User.CAN_MANAGE])
        self.create_user("test", [2])
        self.create_user("test2", [2])
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "test",
                        "locked_out": "1",
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
        for key, value in {
            "username": {"info": "done", "value": "test", "id": 2},
            "locked_out": {"info": "done", "value": True},
            "groups": [{"id": 1, "info": "generated", "value": "default"}],
        }.items():
            assert data[key] == value

    def json_upload_update_locked_out_on_can_manage_auto_overwrite_group(
        self,
    ) -> None:
        self.create_meeting()
        self.create_meeting(5)
        self.set_models(
            {
                "meeting/1": {"group_ids": [1, 2, 3, 4]},
                "group/1": {"meeting_id": 1, "name": "default"},
                "group/2": {"meeting_id": 1, "name": "admin"},
                "group/3": {"meeting_id": 1, "name": "can_manage"},
                "group/4": {"meeting_id": 1, "name": "can_update"},
            }
        )
        self.add_group_permissions(3, [Permissions.User.CAN_MANAGE])
        self.add_group_permissions(4, [Permissions.User.CAN_UPDATE])
        self.add_group_permissions(7, [Permissions.User.CAN_MANAGE])
        self.create_user("test", [3])
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [
                    {
                        "username": "test",
                        "locked_out": "1",
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
        for key, value in {
            "username": {"info": "done", "value": "test", "id": 2},
            "locked_out": {"info": "done", "value": True},
            "groups": [{"id": 1, "info": "generated", "value": "default"}],
        }.items():
            assert data[key] == value
