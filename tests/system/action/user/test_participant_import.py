from typing import Any, Dict

from openslides_backend.action.mixins.import_mixins import ImportMixin, ImportState
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase

from .test_participant_json_upload import ParticipantJsonUploadForUseInImport


class ParticipantImport(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.import_preview1_data: Dict[str, Any] = {
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
                                "value": "male",
                                "info": ImportState.DONE,
                            },
                        },
                    },
                ],
            },
        }

        self.set_models(
            {
                "import_preview/1": self.import_preview1_data,
                "meeting/1": {"is_active_in_organization_id": 1, "group_ids": [1]},
                "group/1": {"name": "group1", "meeting_id": 1},
            }
        )

    def test_import_without_any_group_in_import_data(self) -> None:
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
                "gender": "male",
                "last_name": "Tester",
                "email": "email@test.com",
            },
        )

    def get_import_preview_data(
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
            f"import_preview/{number}": {
                "state": get_import_state(),
                "name": "participant",
                "result": {
                    "meeting_id": 1,
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
        response = self.request("participant.import", {"id": 7, "import": True})
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
        response = self.request("participant.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: saml_id 'testsaml' found in different id (1 instead of None)"
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
        response = self.request("participant.import", {"id": 6, "import": True})
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
        response = self.request("participant.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == [
            "Error: user 111 not found anymore for updating user 'fred'."
        ]

    def test_import_error_state_done_search_data_error(self) -> None:
        self.set_models(
            {
                "import_preview/7": {
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
        response = self.request("participant.import", {"id": 7, "import": True})
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.ERROR
        for i in range(2):
            entry = result["rows"][i]
            assert entry["state"] == ImportState.ERROR
            assert entry["messages"] == [
                "Error: username 'durban' is duplicated in import."
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
        self.import_preview1_data["result"]["rows"][0]["data"]["groups"] = [
            {"info": ImportState.DONE, "value": "group1", "id": 1}
        ]
        self.update_model("import_preview/1", self.import_preview1_data)
        self.base_permission_test(
            {},
            "participant.import",
            {"id": 1, "import": True},
            Permissions.User.CAN_MANAGE,
        )


class ParticipantJsonImportWithIncludedJsonUpload(ParticipantJsonUploadForUseInImport):
    def test_upload_import_with_generated_usernames_okay(self) -> None:
        self.json_upload_saml_id_new()
        response_import = self.request("participant.import", {"id": 1, "import": True})
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
        response_import = self.request("participant.import", {"id": 1, "import": True})
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

    def test_json_upload_update_saml_id_in_existing_participant(self) -> None:
        self.json_upload_update_saml_id_in_existing_participant()
        response_import = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
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
        response_import = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        row = response_import.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["messages"] == [
            "Will remove password and default_password and forbid changing your OpenSlides password.",
        ]
        assert row["data"] == {
            "id": 10,
            "username": {"id": 10, "info": "done", "value": "user10"},
            "saml_id": {"info": "new", "value": "saml_id10"},
            "default_password": {"info": "warning", "value": ""},
            "is_present": False,
            "vote_weight": "2.800000",
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
            "structure_level": "new sl",
            "number": "new number",
            "comment": "new comment",
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
                "structure_level": "new sl",
            },
        )

    def test_json_upload_error_set_saml_id(self) -> None:
        self.json_upload_username_set_saml_id_remove_presence()
        self.set_models({"user/11": {"saml_id": "saml_id10"}})
        response_import = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        row = response_import.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Will remove password and default_password and forbid changing your OpenSlides password.",
            "Error: saml_id 'saml_id10' found in different id (11 instead of 10)",
        ]
        assert row["data"] == {
            "id": 10,
            "username": {"id": 10, "info": "done", "value": "user10"},
            "saml_id": {"info": "error", "value": "saml_id10"},
            "default_password": {"info": "warning", "value": ""},
            "is_present": False,
            "vote_weight": "2.800000",
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
            "structure_level": "new sl",
            "number": "new number",
            "comment": "new comment",
        }

    def test_json_upload_user_not_found_anymore(
        self,
    ) -> None:
        self.json_upload_username_username_and_saml_id_found()
        self.request("user.delete", {"id": 11})
        assert self.assert_model_deleted("user/11")
        response_import = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        row = response_import.json["results"][0][0]["rows"][0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Error: user 11 not found anymore for updating user 'user11'."
        ]
        assert row["data"] == {
            "id": 11,
            "saml_id": {"info": "done", "value": "saml_id11"},
            "username": {"id": 11, "info": ImportState.ERROR, "value": "user11"},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

    def test_json_upload_update_multiple_users_okay(self) -> None:
        self.json_upload_multiple_users()
        response_import = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
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
            },
        )
        self.assert_model_exists(
            "meeting_user/38",
            {
                "user_id": 2,
                "group_ids": [3],
                "meeting_id": 1,
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
                "group_ids": [1],
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
            },
        )
        self.assert_model_exists(
            "meeting_user/35",
            {
                "user_id": 5,
                "group_ids": [1],
                "meeting_id": 1,
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
            },
        )
        self.assert_model_exists(
            "meeting_user/36",
            {
                "user_id": 6,
                "group_ids": [1],
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
            },
        )
        self.assert_model_exists(
            "meeting_user/37",
            {
                "user_id": 7,
                "group_ids": [2, 7],
                "meeting_id": 1,
            },
        )

    def test_json_upload_update_multiple_users_all_error(self) -> None:
        self.json_upload_multiple_users()
        self.request("user.delete", {"id": 2})
        self.request("user.update", {"id": 3, "meeting_id": 1, "group_ids": [1]})
        self.set_models(
            {
                "group/1": {"admin_group_for_meeting_id": 1},
                "group/2": {"admin_group_for_meeting_id": None},
                "group/7": {"name": "changed"},
            }
        )
        self.request_multi("group.delete", [{"id": 2}, {"id": 3}])
        self.assert_model_deleted("group/2")
        self.assert_model_deleted("group/3")
        self.set_models(
            {
                "user/4": {"username": "user4_married"},
                "user/11": {"username": "new_user_5", "saml_id": "saml5"},
                "user/12": {"username": "doubler6", "saml_id": "new_saml6"},
            },
        )
        response_import = self.request("participant.import", {"id": 1, "import": True})
        self.assert_status_code(response_import, 200)
        assert (result := response_import.json["results"][0][0])[
            "state"
        ] == ImportState.ERROR
        row = result["rows"][0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Will remove password and default_password and forbid changing your OpenSlides password.",
            "Following groups were not found: 'group4'",
            "Error: user 2 not found anymore for updating user 'user2'.",
            "Group '3 group3' don't exist anymore",
            "Error in groups: No valid group found inside the pre checked groups from import, see warnings.",
        ]
        assert row["data"] == {
            "id": 2,
            "saml_id": {"info": ImportState.NEW, "value": "test_saml_id2"},
            "username": {"id": 2, "info": ImportState.ERROR, "value": "user2"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "groups": [
                {"id": 3, "info": "error", "value": "group3"},
                {"info": "warning", "value": "group4"},
            ],
        }

        row = result["rows"][1]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Will remove password and default_password and forbid changing your OpenSlides password.",
            "Group '3 group3' don't exist anymore",
            "Error in groups: No valid group found inside the pre checked groups from import, see warnings.",
        ]
        assert row["data"] == {
            "id": 3,
            "saml_id": {"info": ImportState.DONE, "value": "saml3"},
            "username": {"id": 3, "info": ImportState.DONE, "value": "user3"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "vote_weight": "3.345678",
            "can_change_own_password": False,
            "groups": [{"id": 3, "info": "error", "value": "group3"}],
        }

        row = result["rows"][2]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Following groups were not found: 'group4'",
            "Error: user 4 not found anymore for updating user 'user4'.",
        ]
        assert row["data"] == {
            "id": 4,
            "email": "mlk@america.com",
            "username": {"id": 4, "info": ImportState.ERROR, "value": "user4"},
            "last_name": "Luther King",
            "first_name": "Martin",
            "groups": [
                {"info": "warning", "value": "group4"},
                {"id": 1, "info": "generated", "value": "group1"},
            ],
        }

        row = result["rows"][3]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Will remove password and default_password and forbid changing your OpenSlides password.",
            "Error: saml_id 'saml5' found in different id (11 instead of None)",
        ]
        assert row["data"] == {
            "username": {"info": ImportState.DONE, "value": "new_user5"},
            "saml_id": {"info": ImportState.ERROR, "value": "saml5"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "groups": [{"id": 1, "info": "generated", "value": "group1"}],
        }

        row = result["rows"][4]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Will remove password and default_password and forbid changing your OpenSlides password.",
            "Following groups were not found: 'group4'",
            "Error: saml_id 'new_saml6' found in different id (12 instead of None)",
        ]
        assert row["data"] == {
            "username": {"info": ImportState.GENERATED, "value": "new_saml6"},
            "saml_id": {"info": ImportState.ERROR, "value": "new_saml6"},
            "default_password": {"info": ImportState.WARNING, "value": ""},
            "groups": [
                {"info": "warning", "value": "group4"},
                {"id": 1, "info": "generated", "value": "group1"},
            ],
        }

        row = result["rows"][5]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Following groups were not found: 'group4, unknown'",
            "Group '2 group2' don't exist anymore",
            "Expected group '7 group7M1' changed it's name to 'changed'.",
            "Error in groups: No valid group found inside the pre checked groups from import, see warnings.",
        ]
        assert row["data"]["username"] == {
            "info": ImportState.GENERATED,
            "value": "JoanBaez7",
        }
        assert row["data"]["groups"] == [
            {"id": 2, "info": "error", "value": "group2"},
            {"info": "warning", "value": "group4"},
            {"info": "warning", "value": "unknown"},
            {"id": 7, "info": "warning", "value": "group7M1"},
        ]
