from typing import Any

from openslides_backend.action.mixins.import_mixins import ImportState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase

from .test_participant_json_upload import ParticipantJsonUploadForUseInImport


class ParticipantImport(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.import_preview1_data: dict[str, Any] = {
            "state": ImportState.DONE,
            "name": "participant",
            "result": {
                "meeting_id": 1,
                "rows": [
                    {
                        "state": ImportState.NEW,
                        "messages": [],
                        "data": {
                            "username": {
                                "value": "jonny",
                                "info": ImportState.DONE,
                            },
                            "first_name": {
                                "value": "Testy",
                                "info": ImportState.DONE,
                            },
                            "last_name": {
                                "value": "Tester",
                                "info": ImportState.DONE,
                            },
                            "email": {
                                "value": "email@test.com",
                                "info": ImportState.DONE,
                            },
                            "gender": {
                                "id": 1,
                                "value": "male",
                                "info": ImportState.DONE,
                            },
                            "groups": [
                                {
                                    "id": 1,
                                    "value": "group1",
                                    "info": ImportState.DONE,
                                }
                            ],
                        },
                    },
                ],
            },
        }

        self.set_models(
            {
                "organization/1": {"gender_ids": [1, 2, 3, 4]},
                "gender/1": {"name": "male"},
                "gender/2": {"name": "female"},
                "gender/3": {"name": "diverse"},
                "gender/4": {"name": "non-binary"},
                "import_preview/1": self.import_preview1_data,
                "meeting/1": {
                    "is_active_in_organization_id": 1,
                    "group_ids": [1],
                    "structure_level_ids": [1],
                    "committee_id": 1,
                    "admin_group_id": 2,
                },
                "committee/1": {"meeting_ids": [1], "organization_id": 1},
                "group/1": {"name": "group1", "meeting_id": 1},
                "group/2": {
                    "name": "group2",
                    "meeting_id": 1,
                    "admin_group_for_meeting_id": 1,
                },
                "structure_level/1": {"name": "level", "meeting_id": 1},
            }
        )

    def test_import_without_any_group_in_import_data(self) -> None:
        del self.import_preview1_data["result"]["rows"][0]["data"]["groups"]
        self.update_model("import_preview/1", self.import_preview1_data)
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "There is no group in the data of user 'jonny'. Is there a default group for the meeting?"
        )
        self.assert_model_not_exists("user/2")

    def test_import_abort(self) -> None:
        response = self.request("participant.import", {"id": 1, "import": False})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("import_preview/1")
        self.assert_model_not_exists("user/2")

    def test_import_wrong_invalid_name_in_preview(self) -> None:
        self.update_model("import_preview/1", {"name": "account"})
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 400)
        assert (
            "Wrong id doesn't point on participant import data."
            in response.json["message"]
        )
        self.assert_model_exists("import_preview/1", {"name": "account"})

    def test_import_names_and_email_and_create(self) -> None:
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "jonny",
                "first_name": "Testy",
                "gender_id": 1,
                "last_name": "Tester",
                "email": "email@test.com",
                "meeting_ids": [1],
                "meeting_user_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "user_id": 2,
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_model_exists(
            "group/1",
            {
                "meeting_user_ids": [1],
                "meeting_id": 1,
            },
        )

    def test_import_with_group_created_in_between(self) -> None:
        self.set_models(
            {
                "group/123": {"meeting_id": 1, "name": "2Bcreated"},
                "import_preview/2": {
                    "state": ImportState.DONE,
                    "name": "participant",
                    "result": {
                        "meeting_id": 1,
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "username": {
                                        "value": "friend",
                                        "info": ImportState.DONE,
                                    },
                                    "groups": [
                                        {"info": ImportState.NEW, "value": "2Bcreated"}
                                    ],
                                },
                            },
                        ],
                    },
                },
            }
        )
        response = self.request("participant.import", {"id": 2, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "friend",
                "meeting_user_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "user_id": 2,
                "meeting_id": 1,
                "group_ids": [123],
            },
        )

    def test_import_saml_id_error_new_and_saml_id_exists(self) -> None:
        """Set saml_id 'testsaml' to user 1, add the import user 1 will be
        found and the import should result in an error."""
        self.import_preview1_data["result"]["rows"][0]["data"]["username"] = {
            "value": "testuser",
            "info": ImportState.NEW,
        }
        self.import_preview1_data["result"]["rows"][0]["data"]["saml_id"] = {
            "value": "testsaml",
            "info": ImportState.NEW,
        }
        self.set_models(
            {
                "user/1": {"saml_id": "testsaml"},
                "import_preview/1": self.import_preview1_data,
            }
        )
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: saml_id 'testsaml' found in different id (1 instead of None)"
        ]

    def test_import_gender_warning(self) -> None:
        """Set saml_id 'testsaml' to user 1, add the import user 1 will be
        found and the import should result in an error."""
        self.import_preview1_data["result"]["rows"][0]["data"]["gender"] = {
            "value": "notAGender",
            "info": ImportState.WARNING,
        }
        self.import_preview1_data["result"]["rows"][0]["messages"] = [
            "Gender 'notAGender' is not in the allowed gender list."
        ]
        self.set_models({"import_preview/1": self.import_preview1_data})
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.NEW
        assert entry["messages"] == [
            "Gender 'notAGender' is not in the allowed gender list."
        ]
        user = self.assert_model_exists(
            "user/2", {"username": "jonny", "first_name": "Testy"}
        )
        assert user.get("gender_id") is None

    def test_import_error_state_done_missing_username(self) -> None:
        self.import_preview1_data["result"]["rows"][0]["data"].pop("username")
        self.update_model("import_preview/1", self.import_preview1_data)
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Invalid JsonUpload data: The data from json upload must contain a valid username object",
            response.json["message"],
        )

    def test_import_error_state_done_missing_user_in_db(self) -> None:
        self.import_preview1_data["result"]["rows"][0]["data"]["username"] = {
            "value": "fred",
            "info": ImportState.DONE,
            "id": 111,
        }
        self.import_preview1_data["result"]["rows"][0]["data"]["id"] = 111
        self.update_model("import_preview/1", self.import_preview1_data)
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: participant 111 not found anymore for updating participant 'fred'."
        ]

    def test_import_error_state_import_preview(self) -> None:
        self.update_model("import_preview/1", {"state": ImportState.ERROR})
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 400)
        assert response.json["message"] == "Error in import. Data will not be imported."
        self.assert_model_exists("import_preview/1")

    def test_import_no_permission(self) -> None:
        self.base_permission_test({}, "participant.import", {"id": 1, "import": True})

    def test_import_permission(self) -> None:
        self.base_permission_test(
            {},
            "participant.import",
            {"id": 1, "import": True},
            Permissions.User.CAN_MANAGE,
        )

    def test_import_permission_2(self) -> None:
        self.base_permission_test(
            {},
            "participant.import",
            {"id": 1, "import": True},
            Permissions.User.CAN_UPDATE,
            True,
        )

    def test_import_permission_meeting_admin(self) -> None:
        self.import_preview1_data["result"]["rows"][0]["data"]["id"] = 1
        self.import_preview1_data["result"]["rows"][0]["state"] = ImportState.DONE
        self.import_preview1_data["result"]["rows"][0]["data"]["gender"][
            "info"
        ] = ImportState.REMOVE
        self.update_model("import_preview/1", self.import_preview1_data)

        self.create_meeting()
        self.create_meeting(4)
        user_id = self.create_user_for_meeting(1)
        other_user_id = 3
        self.set_models(
            {
                f"user/{other_user_id}": self._get_user_data("jonny", {1: [], 4: []}),
            }
        )
        self.set_user_groups(user_id, [2])
        self.set_user_groups(other_user_id, [1, 4])
        self.login(user_id)

        response = self.request("participant.import", {"id": 1, "import": True})

        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/3", {"user_id": 3, "meeting_id": 4})
        self.assert_model_not_exists("meeting_user/4")

    def test_import_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {}, "participant.import", {"id": 1, "import": True}
        )


class ParticipantJsonImportWithIncludedJsonUpload(ParticipantJsonUploadForUseInImport):
    def test_upload_import_invalid_vote_weight_with_remove(self) -> None:
        self.json_upload_invalid_vote_weight_with_remove()
        response = self.request("participant.import", {"id": 1, "import": True})
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
        self.assert_model_exists(
            "user/2",
            {
                "username": "wilhelm",
                "first_name": "Wilhelm",
                "last_name": "Aberhatnurhut",
                "email": "will@helm.hut",
                "default_password": "123",
                "meeting_user_ids": [12],
            },
        )
        self.assert_model_exists(
            "meeting_user/12",
            {
                "vote_weight": None,
                "group_ids": [1],
            },
        )

    def test_upload_import_with_generated_usernames_okay(self) -> None:
        self.json_upload_saml_id_new()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
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

        group7 = self.assert_model_exists(
            "group/7",
            {
                "id": 7,
                "name": "group4",
                "weight": 1,
                "meeting_id": 1,
                "meeting_user_ids": [2],
            },
        )
        assert "permissions" not in group7

        self.assert_model_not_exists("import_preview/1")

    def test_upload_import_with_generated_usernames_error_username(self) -> None:
        self.json_upload_saml_id_new()
        self.set_models({"user/33": {"username": "test_saml_id21"}})
        response = self.request("participant.import", {"id": 1, "import": True})
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

    def test_json_upload_set_saml_id_in_existing_participant(self) -> None:
        self.json_upload_set_saml_id_in_existing_participant()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
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

    def test_json_upload_update_saml_id_in_existing_participant(self) -> None:
        self.json_upload_update_saml_id_in_existing_participant()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "test",
                "saml_id": "new_one",
                "meeting_user_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "user_id": 2,
                "meeting_id": 1,
                "group_ids": [1],
            },
        )

        self.assert_model_not_exists("import_preview/1")

    def test_json_upload_set_saml_id_remove_presence(self) -> None:
        self.json_upload_username_set_saml_id_remove_presence()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
        ]
        assert row["data"] == {
            "id": 10,
            "username": {"id": 10, "info": ImportState.DONE, "value": "user10"},
            "saml_id": {"info": ImportState.NEW, "value": "saml_id10"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "is_present": {"info": ImportState.DONE, "value": False},
            "vote_weight": {"info": ImportState.DONE, "value": "2.800000"},
            "groups": [{"id": 1, "info": ImportState.GENERATED, "value": "group1"}],
            "structure_level": [{"info": ImportState.DONE, "value": "new sl", "id": 2}],
            "number": {"info": ImportState.DONE, "value": "new number"},
            "comment": {"info": ImportState.DONE, "value": "new comment"},
        }
        self.assert_model_exists(
            "user/10",
            {
                "saml_id": "saml_id10",
                "username": "user10",
                "default_password": "",
                "meeting_user_ids": [110],
                "is_present_in_meeting_ids": [],
            },
        )
        self.assert_model_exists(
            "meeting_user/110",
            {
                "number": "new number",
                "comment": "new comment",
                "group_ids": [1],
                "vote_weight": "2.800000",
                "structure_level_ids": [2],
            },
        )

    def test_json_upload_error_set_saml_id(self) -> None:
        self.json_upload_username_set_saml_id_remove_presence()
        self.set_models({"user/11": {"saml_id": "saml_id10"}})
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Error: saml_id 'saml_id10' found in different id (11 instead of 10)",
        ]
        assert row["data"] == {
            "id": 10,
            "username": {"id": 10, "info": "done", "value": "user10"},
            "saml_id": {"info": "error", "value": "saml_id10"},
            "default_password": {"info": "warning", "value": ""},
            "is_present": {"info": "done", "value": False},
            "vote_weight": {"info": "done", "value": "2.800000"},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
            "structure_level": [{"info": "done", "value": "new sl", "id": 2}],
            "number": {"info": "done", "value": "new number"},
            "comment": {"info": "done", "value": "new comment"},
        }

    def test_json_upload_user_not_found_anymore(
        self,
    ) -> None:
        self.json_upload_username_username_and_saml_id_found()
        self.request("user.delete", {"id": 11})
        self.assert_model_not_exists("user/11")
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Error: participant 11 not found anymore for updating participant 'user11'."
        ]
        assert row["data"] == {
            "id": 11,
            "saml_id": {"info": "done", "value": "saml_id11"},
            "username": {"id": 11, "info": ImportState.ERROR, "value": "user11"},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

    def test_json_upload_update_multiple_users_okay(self) -> None:
        self.json_upload_multiple_users()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        created_groups = {
            self.assert_model_exists(f"group/{id_}")["name"]: id_ for id_ in [9, 10, 11]
        }
        assert sorted(list(created_groups.keys())) == ["Anonymous", "group4", "unknown"]
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "saml_id": "test_saml_id2",
                "username": "user2",
                "default_password": "",
                "password": "",
                "can_change_own_password": False,
                "meeting_ids": [1],
                "meeting_user_ids": [38],
                "gender_id": 3,
            },
        )
        level_up = self.assert_model_exists("structure_level/1")
        if level_up["name"] == "level up":
            no_5 = self.assert_model_exists("structure_level/2", {"name": "no. 5"})
        else:
            assert level_up["name"] == "no. 5"
            no_5 = level_up
            level_up = self.assert_model_exists(
                "structure_level/2", {"name": "level up"}
            )
        self.assert_model_exists(
            "meeting_user/38",
            {
                "user_id": 2,
                "group_ids": [3, created_groups["group4"]],
                "meeting_id": 1,
                "structure_level_ids": [level_up["id"]],
            },
        )

        self.assert_model_exists(
            "user/3",
            {
                "saml_id": "saml3",
                "username": "user3",
                "default_password": "",
                "can_change_own_password": False,
                "password": "",
                "meeting_user_ids": [31, 34],
                "default_vote_weight": "3.300000",
            },
        )
        self.assert_model_exists(
            "meeting_user/31",
            {
                "user_id": 3,
                "group_ids": [3],
                "meeting_id": 1,
                "vote_weight": "3.345678",
            },
        )

        self.assert_model_exists(
            "user/4",
            {
                "username": "user4",
                "email": "mlk@america.com",
                "first_name": "Martin",
                "last_name": "Luther King",
                "default_password": "secret",
                "default_vote_weight": "4.300000",
                "can_change_own_password": True,
                "meeting_ids": [1],
                "meeting_user_ids": [39],
            },
        )
        self.assert_model_exists(
            "meeting_user/39",
            {
                "user_id": 4,
                "group_ids": [created_groups["group4"]],
                "meeting_id": 1,
                "vote_weight": None,
            },
        )

        self.assert_model_exists(
            "user/5",
            {
                "saml_id": "saml5",
                "username": "new_user5",
                "default_password": "",
                "can_change_own_password": False,
                "meeting_user_ids": [35],
                "is_physical_person": True,
                "is_active": True,
                "gender_id": None,
            },
        )
        self.assert_model_exists(
            "meeting_user/35",
            {
                "user_id": 5,
                "group_ids": [1],
                "meeting_id": 1,
                "structure_level_ids": [level_up["id"], no_5["id"]],
            },
        )

        self.assert_model_exists(
            "user/6",
            {
                "id": 6,
                "saml_id": "new_saml6",
                "username": "new_saml6",
                "default_password": "",
                "default_vote_weight": "1.000000",
                "can_change_own_password": False,
                "meeting_user_ids": [36],
                "is_physical_person": True,
                "is_active": True,
            },
        )
        self.assert_model_exists(
            "meeting_user/36",
            {
                "user_id": 6,
                "group_ids": [created_groups["group4"]],
                "meeting_id": 1,
            },
        )

        self.assert_model_exists(
            "user/7",
            {
                "id": 7,
                "username": "JoanBaez7",
                "first_name": "Joan",
                "last_name": "Baez7",
                "can_change_own_password": True,
                "meeting_user_ids": [37],
                "is_physical_person": True,
                "is_active": True,
                "gender_id": 2,
            },
        )
        self.assert_model_exists(
            "meeting_user/37",
            {
                "user_id": 7,
                "group_ids": [
                    2,
                    created_groups["group4"],
                    created_groups["Anonymous"],
                    created_groups["unknown"],
                    7,
                ],
                "meeting_id": 1,
            },
        )

    def test_json_upload_one_structure_level_newly_created(self) -> None:
        self.json_upload_multiple_users()
        self.request("structure_level.create", {"meeting_id": 1, "name": "no. 5"})
        response = self.request("participant.import", {"id": 1, "import": True})
        created_groups = {
            self.assert_model_exists(f"group/{id_}")["name"]: id_ for id_ in [9, 10, 11]
        }
        assert sorted(list(created_groups.keys())) == ["Anonymous", "group4", "unknown"]
        self.assert_status_code(response, 200)
        assert (result := response.json["results"][0][0])["state"] == ImportState.DONE
        row = result["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
        ]
        assert row["data"] == {
            "id": 2,
            "saml_id": {"info": ImportState.NEW, "value": "test_saml_id2"},
            "username": {"id": 2, "info": ImportState.DONE, "value": "user2"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "groups": [
                {"id": 3, "info": "done", "value": "group3"},
                {"id": created_groups["group4"], "info": "new", "value": "group4"},
            ],
            "structure_level": [{"info": "new", "value": "level up", "id": 2}],
            "gender": {"id": 3, "info": "done", "value": "diverse"},
        }

        row = result["rows"][1]
        assert row["state"] == ImportState.DONE
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
        ]
        assert row["data"] == {
            "id": 3,
            "saml_id": {"info": ImportState.DONE, "value": "saml3"},
            "username": {"id": 3, "info": ImportState.DONE, "value": "user3"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "vote_weight": {"info": ImportState.DONE, "value": "3.345678"},
            "groups": [{"id": 3, "info": "done", "value": "group3"}],
        }

        row = result["rows"][2]
        assert row["state"] == ImportState.DONE
        assert row["messages"] == []
        assert row["data"] == {
            "id": 4,
            "email": {"value": "mlk@america.com", "info": ImportState.DONE},
            "username": {"id": 4, "info": ImportState.DONE, "value": "user4"},
            "last_name": {"value": "Luther King", "info": ImportState.DONE},
            "first_name": {"value": "Martin", "info": ImportState.DONE},
            "groups": [
                {"id": created_groups["group4"], "info": "new", "value": "group4"}
            ],
        }

        row = result["rows"][3]
        assert row["state"] == ImportState.NEW
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Gender 'unknown' is not in the allowed gender list.",
        ]
        assert row["data"] == {
            "username": {"info": ImportState.DONE, "value": "new_user5"},
            "saml_id": {"info": ImportState.NEW, "value": "saml5"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
            "structure_level": [
                {"info": ImportState.NEW, "value": "level up", "id": 2},
                {"info": ImportState.DONE, "value": "no. 5", "id": 1},
            ],
            "gender": {"info": "warning", "value": "unknown"},
        }

        self.assert_model_exists("structure_level/2", {"name": "level up"})

        row = result["rows"][4]
        assert row["state"] == ImportState.NEW
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
        ]
        assert row["data"] == {
            "username": {"info": ImportState.GENERATED, "value": "new_saml6"},
            "saml_id": {"info": ImportState.NEW, "value": "new_saml6"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "is_present": {"info": "done", "value": True},
            "groups": [
                {"id": created_groups["group4"], "info": "new", "value": "group4"},
            ],
        }

    def test_json_upload_update_multiple_users_all_error(self) -> None:
        self.json_upload_multiple_users()
        self.request("user.delete", {"id": 2})
        self.request("structure_level.create", {"meeting_id": 1, "name": "no. 5"})
        self.set_models(
            {
                "group/1": {"admin_group_for_meeting_id": 1},
                "group/2": {
                    "admin_group_for_meeting_id": None,
                    "meeting_user_ids": None,
                },
                "group/7": {"name": "changed"},
                "meeting_user/31": {"group_ids": [1]},
            }
        )
        self.request_multi("group.delete", [{"id": 2}, {"id": 3}])
        self.assert_model_not_exists("group/2")
        self.assert_model_not_exists("group/3")
        self.set_models(
            {
                "user/4": {"username": "user4_married"},
                "user/11": {"username": "new_user_5", "saml_id": "saml5"},
                "user/12": {"username": "doubler6", "saml_id": "new_saml6"},
            },
        )
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)

        self.assert_model_not_exists("structure_level/2")

        assert (result := response.json["results"][0][0])["state"] == ImportState.ERROR
        row = result["rows"][0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Error: participant 2 not found anymore for updating participant 'user2'.",
            "The group '3 group3' doesn't exist anymore.",
        ]
        assert row["data"] == {
            "id": 2,
            "saml_id": {"info": ImportState.NEW, "value": "test_saml_id2"},
            "username": {"id": 2, "info": ImportState.ERROR, "value": "user2"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "groups": [
                {"id": 3, "info": "warning", "value": "group3"},
                {"info": "new", "value": "group4"},
            ],
            "structure_level": [{"info": "new", "value": "level up"}],
            "gender": {"id": 3, "info": "done", "value": "diverse"},
        }

        row = result["rows"][1]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "The group '3 group3' doesn't exist anymore.",
            "Error in groups: No valid group found inside the pre-checked groups from import, see warnings.",
        ]
        assert row["data"] == {
            "id": 3,
            "saml_id": {"info": ImportState.DONE, "value": "saml3"},
            "username": {"id": 3, "info": ImportState.DONE, "value": "user3"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "vote_weight": {"info": ImportState.DONE, "value": "3.345678"},
            "groups": [{"id": 3, "info": "error", "value": "group3"}],
        }

        row = result["rows"][2]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Error: participant 4 not found anymore for updating participant 'user4'.",
        ]
        assert row["data"] == {
            "id": 4,
            "email": {"value": "mlk@america.com", "info": ImportState.DONE},
            "username": {"id": 4, "info": ImportState.ERROR, "value": "user4"},
            "last_name": {"value": "Luther King", "info": ImportState.DONE},
            "first_name": {"value": "Martin", "info": ImportState.DONE},
            "groups": [
                {"info": "new", "value": "group4"},
            ],
        }

        row = result["rows"][3]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Gender 'unknown' is not in the allowed gender list.",
            "Error: saml_id 'saml5' found in different id (11 instead of None)",
        ]
        assert row["data"] == {
            "username": {"info": ImportState.DONE, "value": "new_user5"},
            "saml_id": {"info": ImportState.ERROR, "value": "saml5"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
            "structure_level": [
                {"info": ImportState.NEW, "value": "level up"},
                {"info": ImportState.NEW, "value": "no. 5"},
            ],
            "gender": {"info": "warning", "value": "unknown"},
        }

        row = result["rows"][4]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Error: saml_id 'new_saml6' found in different id (12 instead of None)",
        ]
        assert row["data"] == {
            "username": {"info": ImportState.GENERATED, "value": "new_saml6"},
            "saml_id": {"info": ImportState.ERROR, "value": "new_saml6"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "is_present": {"info": "done", "value": True},
            "groups": [
                {"info": "new", "value": "group4"},
            ],
        }

        row = result["rows"][5]
        assert row["state"] == ImportState.NEW
        assert row["messages"] == [
            "The group '2 group2' doesn't exist anymore.",
            "The group '7 group7M1' changed its name to 'changed'.",
        ]
        assert row["data"]["username"] == {
            "info": ImportState.GENERATED,
            "value": "JoanBaez7",
        }
        assert row["data"]["groups"] == [
            {"id": 2, "info": "warning", "value": "group2"},
            {"info": "new", "value": "group4"},
            {"info": "new", "value": "Anonymous"},
            {"info": "new", "value": "unknown"},
            {"id": 7, "info": "warning", "value": "group7M1"},
        ]

    def test_json_upload_with_complicated_names(self) -> None:
        self.json_upload_with_complicated_names()
        response_import = self.request("participant.import", {"id": 1, "import": True})
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

    def test_json_upload_with_sufficient_field_permission_update(self) -> None:
        """fields in preview forbidden, in import allowed => okay"""
        self.json_upload_not_sufficient_field_permission_update()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, 1
        )
        self.set_committee_management_level([60], 1)
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Account is added to the meeting, but changes to the following field(s) are not possible: username, first_name, email, saml_id, default_password",
            "In contrast to preview you may import field(s) 'email, first_name, saml_id, username'",
        ]
        assert row["data"] == {
            "id": 2,
            "saml_id": {"info": "done", "value": "saml_id1"},
            "username": {"id": 2, "info": "done", "value": "user2"},
            "first_name": {"info": "done", "value": "Jim"},
            "email": {"info": "done", "value": "Jim.Knopf@Lummer.land"},
            "vote_weight": {"info": "done", "value": "1.234560"},
            "default_password": {"info": "remove", "value": ""},
            "groups": [
                {"id": 1, "info": "done", "value": "group1"},
                {"id": 2, "info": "done", "value": "group2"},
                {"id": 3, "info": "done", "value": "group3"},
                {"id": 7, "info": "new", "value": "group4"},
            ],
        }
        self.assert_model_exists(
            "user/2",
            {
                "username": "user2",
                "saml_id": "saml_id1",
                "first_name": "Jim",
                "meeting_user_ids": [11, 44],
                "meeting_ids": [1, 4],
                "committee_ids": [60],
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
                "default_password": "",
                "can_change_own_password": False,
                "password": "",
            },
        )
        self.assert_model_exists(
            "meeting_user/11",
            {"vote_weight": "1.234560", "group_ids": [1, 2, 3, 7]},
        )

    def test_json_upload_less_fields_field_permission_update(self) -> None:
        """fields in preview allowed, in import forbidden => error"""
        self.json_upload_not_sufficient_field_permission_update()
        self.assert_model_exists(
            "user/2",
            {
                "first_name": "John",
                "saml_id": None,
                "default_password": "secret",
                "can_change_own_password": True,
            },
        )
        self.assert_model_exists("meeting_user/11", {"vote_weight": None})
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Account is added to the meeting, but changes to the following field(s) are not possible: username, first_name, email, saml_id, default_password",
        ]
        assert row["data"] == {
            "id": 2,
            "saml_id": {"info": "remove", "value": "saml_id1"},
            "username": {"id": 2, "info": "remove", "value": "user2"},
            "first_name": {"info": "remove", "value": "Jim"},
            "email": {"info": "remove", "value": "Jim.Knopf@Lummer.land"},
            "vote_weight": {"info": "done", "value": "1.234560"},
            "default_password": {"info": "remove", "value": ""},
            "groups": [
                {"id": 1, "info": "done", "value": "group1"},
                {"id": 2, "info": "done", "value": "group2"},
                {"id": 3, "info": "done", "value": "group3"},
                {"id": 7, "info": "new", "value": "group4"},
            ],
        }
        self.assert_model_exists(
            "user/2",
            {
                "username": "user2",
                "first_name": "John",
                "meeting_user_ids": [11, 44],
                "meeting_ids": [1, 4],
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
                "default_password": "secret",
                "can_change_own_password": True,
                "password": "secretcrypted",
            },
        )
        self.assert_model_exists(
            "meeting_user/11",
            {
                "user_id": 2,
                "vote_weight": "1.234560",
                "group_ids": [1, 2, 3, 7],
            },
        )

    def test_json_upload_less_fields_field_permission_update_with_member_number(
        self,
    ) -> None:
        self.json_upload_not_sufficient_field_permission_update_with_member_number()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Account is added to the meeting, but changes to the following field(s) are not possible: member_number, first_name, email, username, saml_id, default_password",
        ]
        assert row["data"] == {
            "id": 2,
            "saml_id": {"info": "remove", "value": "saml_id1"},
            "username": {"info": "remove", "value": "user2"},
            "first_name": {"info": "remove", "value": "Jim"},
            "email": {"info": "remove", "value": "Jim.Knopf@Lummer.land"},
            "vote_weight": {"info": "done", "value": "1.234560"},
            "default_password": {"info": "remove", "value": ""},
            "groups": [
                {"id": 1, "info": "done", "value": "group1"},
                {"id": 2, "info": "done", "value": "group2"},
                {"id": 3, "info": "done", "value": "group3"},
                {"id": 7, "info": "new", "value": "group4"},
            ],
            "member_number": {"id": 2, "value": "M3MNUM", "info": "remove"},
        }
        self.assert_model_exists(
            "user/2",
            {
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
        )
        self.assert_model_exists(
            "meeting_user/11",
            {
                "user_id": 2,
                "vote_weight": "1.234560",
                "group_ids": [1, 2, 3, 7],
            },
        )

    def test_json_upload_sufficient_field_permission_create(self) -> None:
        self.json_upload_sufficient_field_permission_create()
        self.set_models(
            {
                "meeting_user/1": {"group_ids": []},
                "group/3": {"meeting_user_ids": []},
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
                },
            }
        )
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Error: In contrast to preview you may not import field(s) 'vote_weight'",
        ]
        assert row["data"] == {
            "saml_id": {"info": "new", "value": "saml_id1"},
            "username": {"info": "done", "value": "user2"},
            "first_name": {"info": "done", "value": "Jim"},
            "vote_weight": {"info": "error", "value": "1.234560"},
            "default_password": {"info": "warning", "value": ""},
            "groups": [
                {"id": 1, "info": "done", "value": "group1"},
                {"id": 2, "info": "done", "value": "group2"},
                {"id": 3, "info": "done", "value": "group3"},
                {"info": "new", "value": "group4"},
            ],
        }

    def test_json_upload_legacy_username(self) -> None:
        self.json_upload_legacy_username()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)

    def test_reupload_with_structure_level(self) -> None:
        import_data = {
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
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [import_data.copy()],
            },
        )
        self.assert_status_code(response, 200)
        response = self.request(
            "participant.import",
            {"id": response.json["results"][0][0].get("id"), "import": True},
        )
        self.assert_status_code(response, 200)
        response = self.request(
            "participant.json_upload",
            {
                "meeting_id": 1,
                "data": [import_data],
            },
        )
        self.assert_status_code(response, 200)
        response = self.request(
            "participant.import",
            {"id": response.json["results"][0][0].get("id"), "import": True},
        )
        self.assert_status_code(response, 200)

    def test_json_upload_set_member_number_in_existing_participants(self) -> None:
        self.json_upload_set_member_number_in_existing_participants()
        response = self.request("participant.import", {"id": 1, "import": True})
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

    def test_json_upload_set_other_matching_criteria_in_existing_participant_via_member_number(
        self,
    ) -> None:
        self.json_upload_set_other_matching_criteria_in_existing_participant_via_member_number()
        response = self.request("participant.import", {"id": 1, "import": True})
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
            },
        )

    def test_json_upload_try_to_update_to_username_that_was_created_in_between(
        self,
    ) -> None:
        self.json_upload_set_other_matching_criteria_in_existing_participant_via_member_number()
        self.create_user("newname")
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Because this participant is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides.",
            "Error: username 'newname' found in different id (3 instead of 2)",
        ]
        assert row["data"] == {
            "id": 2,
            "default_password": {"value": "", "info": "warning"},
            "username": {"info": "error", "value": "newname"},
            "saml_id": {"info": "new", "value": "some_other_saml"},
            "first_name": {"info": "done", "value": "second"},
            "last_name": {"info": "done", "value": "second_to_last"},
            "member_number": {"info": "done", "value": "M3MNUM", "id": 2},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

    def test_json_upload_add_member_number(self) -> None:
        self.json_upload_add_member_number()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "username": "test",
                "member_number": "old_one",
                "default_vote_weight": "2.300000",
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "user_id": 2,
                "vote_weight": "4.345678",
            },
        )

    def test_json_upload_new_participant_with_member_number(self) -> None:
        self.json_upload_new_participant_with_member_number()
        response = self.request("participant.import", {"id": 1, "import": True})
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

    def test_json_upload_dont_recognize_empty_name_and_email(self) -> None:
        self.json_upload_dont_recognize_empty_name_and_email()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/5",
            {
                "username": "balubear",
                "member_number": "mem_nr",
            },
        )

    def test_json_upload_remove_last_admin_add_a_new_one(self) -> None:
        self.json_upload_remove_last_admin_add_a_new_one()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["messages"] == []
        row = response.json["results"][0][0]["rows"][1]
        assert row["state"] == ImportState.NEW
        assert row["messages"] == []

    def test_json_upload_remove_admin_group(self) -> None:
        self.json_upload_remove_admin_group_normal()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["messages"] == []

    def test_json_upload_remove_last_admin_in_template(self) -> None:
        self.json_upload_remove_last_admin_in_template()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["messages"] == []

    def test_json_upload_remove_admin_group_error(self) -> None:
        self.json_upload_remove_admin_group_normal()
        self.set_models(
            {
                "meeting_user/2": {"group_ids": [3]},
                "group/2": {"meeting_user_ids": [1]},
                "group/3": {"meeting_user_ids": [2]},
            }
        )
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == ["Error: Cannot remove last member of admin group"]

    def test_json_upload_remove_last_admin_in_ex_template_error(self) -> None:
        self.json_upload_remove_last_admin_in_template()
        self.set_models(
            {
                "meeting/1": {"template_for_organization_id": None},
                "organization/1": {"template_meeting_ids": None},
            }
        )
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == ["Error: Cannot remove last member of admin group"]

    def test_json_upload_permission_as_locked_out(self) -> None:
        self.json_upload_dont_recognize_empty_name_and_email()
        meeting_user_id = self.set_user_groups(1, [2])[0]
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
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action participant.import. Missing permissions: Permission user.can_manage in meeting 1 or OrganizationManagementLevel can_manage_organization in organization 1 or CommitteeManagementLevel can_manage in committee 1",
            response.json["message"],
        )

    def test_json_upload_multi_with_locked_out(self) -> None:
        self.json_upload_multi_with_locked_out()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/1", {"user_id": 2, "meeting_id": 1, "locked_out": True}
        )
        self.assert_model_exists(
            "meeting_user/2", {"user_id": 4, "meeting_id": 1, "locked_out": True}
        )
        self.assert_model_exists(
            "meeting_user/3", {"user_id": 5, "meeting_id": 5, "locked_out": None}
        )
        self.assert_model_exists(
            "meeting_user/4", {"user_id": 6, "meeting_id": 5, "locked_out": None}
        )
        self.assert_model_exists(
            "meeting_user/5", {"user_id": 7, "meeting_id": 1, "locked_out": True}
        )
        self.assert_model_exists(
            "meeting_user/6", {"user_id": 8, "meeting_id": 1, "locked_out": True}
        )
        self.assert_model_exists(
            "meeting_user/7", {"user_id": 9, "meeting_id": 1, "locked_out": False}
        )
        self.assert_model_exists(
            "meeting_user/8", {"user_id": 10, "meeting_id": 1, "locked_out": False}
        )
        self.assert_model_exists(
            "meeting_user/9", {"user_id": 11, "meeting_id": 1, "locked_out": True}
        )
        self.assert_model_exists(
            "meeting_user/10", {"user_id": 12, "meeting_id": 1, "locked_out": True}
        )
        self.assert_model_exists(
            "meeting_user/11", {"user_id": 3, "meeting_id": 1, "locked_out": True}
        )
        self.assert_model_exists(
            "meeting_user/12", {"user_id": 5, "meeting_id": 1, "locked_out": True}
        )
        self.assert_model_exists(
            "meeting_user/13", {"user_id": 6, "meeting_id": 1, "locked_out": True}
        )

    def test_json_upload_update_locked_out_on_meeting_admin_auto_overwrite_group(
        self,
    ) -> None:
        self.json_upload_update_locked_out_on_meeting_admin_auto_overwrite_group()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0]["state"] == ImportState.DONE
        self.assert_model_exists(
            "meeting_user/1", {"user_id": 2, "meeting_id": 1, "locked_out": True}
        )

    def test_json_upload_update_locked_out_on_can_manage_auto_overwrite_group(
        self,
    ) -> None:
        self.json_upload_update_locked_out_on_can_manage_auto_overwrite_group()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0]["state"] == ImportState.DONE
        self.assert_model_exists(
            "meeting_user/1", {"user_id": 2, "meeting_id": 1, "locked_out": True}
        )

    def test_json_upload_lock_out_self_error(self) -> None:
        self.json_upload_update_locked_out_on_meeting_admin_auto_overwrite_group()
        self.login(2)
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: You may not lock yourself out of a meeting"
        ]

    def test_json_upload_lock_out_orgaadmin(self) -> None:
        self.json_upload_update_locked_out_on_meeting_admin_auto_overwrite_group()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, 2
        )
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: Cannot lock user from meeting 1 as long as he has the OrganizationManagementLevel can_manage_organization"
        ]

    def test_json_upload_lock_out_committeeadmin(self) -> None:
        self.json_upload_update_locked_out_on_meeting_admin_auto_overwrite_group()
        self.set_committee_management_level([60], 2)
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: Cannot lock user out of meeting 1 as he is manager of the meetings committee or one of its parents"
        ]

    def test_json_upload_set_home_committee(self) -> None:
        self.json_upload_set_home_committee()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "meeting_user_ids": [1],
                "username": "Alice",
                "home_committee_id": 1,
                "guest": False,
            },
        )

    def test_json_upload_update_home_committee_and_guest_false(self) -> None:
        self.json_upload_update_home_committee_and_guest_false()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "meeting_user_ids": [1],
                "username": "Alice",
                "home_committee_id": 1,
                "guest": False,
            },
        )

    def test_json_upload_update_guest_true_without_home_committee(self) -> None:
        self.json_upload_update_guest_true()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"id": 2, "meeting_user_ids": [1], "username": "Alice", "guest": True},
        )

    def test_json_upload_update_guest_true_with_home_committee(self) -> None:
        self.json_upload_update_guest_true(with_home_committee=True)
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "meeting_user_ids": [1],
                "username": "Alice",
                "home_committee_id": None,
                "guest": True,
            },
        )

    def test_json_upload_update_guest_true_without_home_committee_perms(self) -> None:
        self.json_upload_update_guest_true(
            with_home_committee=True, has_home_committee_perms=False
        )
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "meeting_user_ids": [1],
                "username": "Alice",
                "first_name": "alice",
                "guest": None,
            },
        )

    def test_json_upload_set_home_committee_no_perms(self) -> None:
        self.json_upload_set_home_committee(has_perm=False)
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "meeting_user_ids": [1],
                "username": "Alice",
                "home_committee_id": None,
            },
        )

    def test_json_upload_update_home_committee_no_perms_new(self) -> None:
        self.json_upload_update_home_committee(new_perm=False)
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "meeting_user_ids": [1],
                "username": "Alice",
                "first_name": "alice",
                "home_committee_id": 1,
            },
        )

    def test_json_upload_update_home_committee_no_perms_both(self) -> None:
        self.json_upload_update_home_committee(old_perm=False, new_perm=False)
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "meeting_user_ids": [1],
                "username": "Alice",
                "first_name": "alice",
                "home_committee_id": 1,
            },
        )

    def test_json_upload_update_home_committee_no_perms_new_anymore(self) -> None:
        self.json_upload_update_home_committee()
        self.set_committee_management_level([1])
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.ERROR
        assert response.json["results"][0][0]["rows"][0]["state"] == ImportState.ERROR
        assert response.json["results"][0][0]["rows"][0]["messages"] == [
            "Error: In contrast to preview you may not import field(s) 'guest, home_committee_id'"
        ]
        assert response.json["results"][0][0]["rows"][0]["data"] == {
            "id": 2,
            "first_name": {
                "info": ImportState.DONE,
                "value": "alice",
            },
            "groups": [
                {
                    "id": 1,
                    "info": ImportState.GENERATED,
                    "value": "group1",
                },
            ],
            "guest": {
                "info": ImportState.ERROR,
                "value": False,
            },
            "home_committee": {
                "id": 2,
                "info": ImportState.ERROR,
                "value": "Home",
            },
            "username": {
                "id": 2,
                "info": ImportState.DONE,
                "value": "Alice",
            },
        }
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "meeting_user_ids": None,
                "username": "Alice",
                "first_name": None,
                "home_committee_id": 1,
            },
        )

    def test_json_upload_update_home_committee_and_guest_false_no_perms_new(
        self,
    ) -> None:
        self.json_upload_update_home_committee_and_guest_false_no_perms_new()
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "meeting_user_ids": [1],
                "username": "Alice",
                "guest": None,
                "home_committee_id": 1,
            },
        )

    def test_json_upload_update_home_committee_and_guest_false_formerly_no_perms_new(
        self,
    ) -> None:
        self.json_upload_update_home_committee_and_guest_false_no_perms_new()
        self.set_committee_management_level([1, 2])
        response = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "id": 2,
                "meeting_user_ids": [1],
                "username": "Alice",
                "guest": False,
                "home_committee_id": 2,
            },
        )
