from openslides_backend.action.mixins.import_mixins import ImportState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class CommitteeJsonUpload(BaseActionTestCase):
    def test_json_upload_create_correct(self) -> None:
        response = self.request(
            "committee.json_upload",
            {"data": [{"name": "test", "description": "A long text"}]},
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {"name": "test", "description": "A long text"},
        }
        self.assert_model_exists(
            "action_worker/1",
            {
                "result": {
                    "import": "committee",
                    "rows": [
                        {
                            "state": ImportState.NEW,
                            "messages": [],
                            "data": {"name": "test", "description": "A long text"},
                        },
                    ],
                },
            },
        )
        assert response.json["results"][0][0]["statistics"][1] == {
            "name": "Committees created",
            "value": 1,
        }
        assert response.json["results"][0][0]["statistics"][2] == {
            "name": "Committees updated",
            "value": 0,
        }

    def test_json_upload_update_correct(self) -> None:
        self.set_models({"committee/7": {"name": "test"}})
        response = self.request("committee.json_upload", {"data": [{"name": "test"}]})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.DONE,
            "messages": [],
            "data": {"name": "test", "id": 7},
        }

    def test_json_upload_duplicate_error(self) -> None:
        self.set_models(
            {"committee/7": {"name": "test"}, "committee/8": {"name": "test"}}
        )
        response = self.request("committee.json_upload", {"data": [{"name": "test"}]})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.ERROR,
            "messages": ["Found more committees with the same name in db."],
            "data": {"name": "test"},
        }

    def test_json_upload_create_duplicate_in_rows(self) -> None:
        """Special case where the same name is in two data entries."""
        response = self.request(
            "committee.json_upload", {"data": [{"name": "n1"}, {"name": "n1"}]}
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {"name": "n1"},
        }
        assert response.json["results"][0][0]["rows"][1] == {
            "state": ImportState.DONE,
            "messages": [],
            "data": {"name": "n1"},
        }

    def test_json_upload_update_duplicate_in_rows_and_db(self) -> None:
        """Special case where the same name is in the db and in two entries."""
        self.set_models({"committee/7": {"name": "n1"}})
        response = self.request(
            "committee.json_upload", {"data": [{"name": "n1"}, {"name": "n1"}]}
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.DONE,
            "messages": [],
            "data": {"name": "n1", "id": 7},
        }
        assert response.json["results"][0][0]["rows"][1] == {
            "state": ImportState.DONE,
            "messages": [],
            "data": {"name": "n1", "id": 7},
        }

    def test_json_upload_organization_tags_duplicates(self) -> None:
        """Duplicate tags in same entry and in a second entry."""
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {"name": "n1", "organization_tags": "ot1, ot2, ot1"},
                    {"name": "n2", "organization_tags": "ot1"},
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": "n1",
                "organization_tags": [
                    {"info": ImportState.NEW, "value": "ot1"},
                    {"info": ImportState.NEW, "value": "ot2"},
                    {"info": ImportState.DONE, "value": "ot1"},
                ],
            },
        }
        assert response.json["results"][0][0]["rows"][1] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": "n2",
                "organization_tags": [{"info": ImportState.DONE, "value": "ot1"}],
            },
        }

    def test_json_upload_organization_tags_special_cases(self) -> None:
        """Duplicate tags in same entry and db."""
        self.set_models(
            {
                "committee/7": {"name": "n1", "organization_tag_ids": [8]},
                "organization_tag/8": {"name": "ot1", "tagged_ids": ["committee/7"]},
            }
        )
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {"name": "n1", "organization_tags": "ot1, ot2, ot1"},
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.DONE,
            "messages": [],
            "data": {
                "name": "n1",
                "id": 7,
                "organization_tags": [
                    {"info": ImportState.DONE, "value": "ot1", "id": 8},
                    {"info": ImportState.NEW, "value": "ot2"},
                    {"info": ImportState.DONE, "value": "ot1", "id": 8},
                ],
            },
        }

    def test_json_upload_empty_field(self) -> None:
        self.set_models(
            {
                "committee/7": {"name": "bar", "user_ids": [4, 5]},
                "user/4": {"username": "bla", "committee_ids": [7]},
                "user/5": {"username": "foo", "committee_ids": [7]},
            }
        )
        response = self.request(
            "committee.json_upload",
            {"data": [{"name": "bar", "committee_managers": ""}]},
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.DONE,
            "messages": [],
            "data": {
                "name": "bar",
                "id": 7,
                "committee_managers": [],
            },
        }

    def test_json_upload_update_list_fields(self) -> None:
        self.set_models(
            {
                "organization_tag/1": {"name": "ot1", "tagged_ids": ["committee/8"]},
                "organization_tag/2": {"name": "ot2", "tagged_ids": ["committee/8"]},
                "committee/3": {
                    "name": "fc1",
                    "receive_forwardings_from_committee_ids": [8],
                },
                "committee/4": {
                    "name": "fc2",
                    "receive_forwardings_from_committee_ids": [8],
                },
                "user/5": {"username": "m1", "committee_ids": [8]},
                "user/6": {"username": "m2", "committee_ids": [8]},
                "committee/8": {
                    "name": "n1",
                    "organization_tag_ids": [1, 2],
                    "user_ids": [5, 6],
                    "forward_to_committee_ids": [3, 4],
                },
            }
        )
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "n1",
                        "organization_tags": "ot1, ot3",
                        "committee_managers": "m1, m3",
                        "forward_to_committees": "fc2, fc3",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.DONE,
            "messages": ["Missing committee manager(s): m3"],
            "data": {
                "name": "n1",
                "id": 8,
                "organization_tags": [
                    {"value": "ot1", "info": ImportState.DONE, "id": 1},
                    {"value": "ot3", "info": ImportState.NEW},
                ],
                "committee_managers": [
                    {"value": "m1", "info": ImportState.DONE, "id": 5},
                    {"value": "m3", "info": ImportState.WARNING},
                ],
                "forward_to_committees": [
                    {"value": "fc2", "info": ImportState.DONE, "id": 4},
                    {"value": "fc3", "info": ImportState.NEW},
                ],
            },
        }

    def test_json_upload_empty_data(self) -> None:
        response = self.request(
            "committee.json_upload",
            {"data": []},
        )
        self.assert_status_code(response, 400)
        assert "data.data must contain at least 1 items" in response.json["message"]

    def test_json_upload_date(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "start_time": "2023-08-09",
                        "end_time": "2023-08-10",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": ["Meeting will be created with meeting.create."],
            "data": {
                "name": "test",
                "meeting_name": "test meeting",
                "start_time": 1691539200,
                "end_time": 1691625600,
            },
        }

    def test_json_upload_start_time_xor_end_time_error_case(self) -> None:
        """check meeting start_time/end_time condition"""
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "start_time": "2023-08-09",
                    },
                    {
                        "name": "test2",
                        "meeting_name": "test meeting 2",
                        "end_time": "2023-08-10",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.ERROR,
            "messages": [
                "Only one of start_time and end_time is not allowed.",
                "Meeting will be created with meeting.create.",
            ],
            "data": {
                "name": "test",
                "meeting_name": "test meeting",
                "start_time": 1691539200,
            },
        }
        assert response.json["results"][0][0]["rows"][1] == {
            "state": ImportState.ERROR,
            "messages": [
                "Only one of start_time and end_time is not allowed.",
                "Meeting will be created with meeting.create.",
            ],
            "data": {
                "name": "test2",
                "meeting_name": "test meeting 2",
                "end_time": 1691625600,
            },
        }

    def test_json_upload_wrong_date(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "start_time": "2023-08-09",
                        "end_time": "12XX-broken",
                    }
                ]
            },
        )
        self.assert_status_code(response, 400)
        assert "Could not parse 12XX-broken except date" in response.json["message"]

    def test_json_upload_meeting_field_but_no_meeting_name(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_template": "testtemplate",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.WARNING,
            "messages": ["No meeting will be created without meeting_name"],
            "data": {
                "name": "test",
                "meeting_template": {
                    "value": "testtemplate",
                    "info": ImportState.WARNING,
                },
            },
        }

    def test_json_upload_meeting_template_not_found(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_template": "test",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": "test",
                "meeting_name": "test meeting",
                "meeting_template": {"value": "test", "info": ImportState.WARNING},
            },
        }

    def test_json_upload_meeting_template_found(self) -> None:
        self.set_models({"meeting/23": {"name": "test"}})
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_template": "test",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": "test",
                "meeting_name": "test meeting",
                "meeting_template": {
                    "value": "test",
                    "info": ImportState.DONE,
                    "id": 23,
                },
            },
        }
        assert response.json["results"][0][0]["statistics"][5] == {
            "name": "Meetings copied from template",
            "value": 1,
        }
        assert response.json["results"][0][0]["statistics"][4] == {
            "name": "Meetings created without template",
            "value": 0,
        }

    def test_json_upload_committee_managers(self) -> None:
        self.set_models({"user/23": {"username": "test"}})
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "committee A",
                        "committee_managers": "test, new",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": ["Missing committee manager(s): new"],
            "data": {
                "name": "committee A",
                "committee_managers": [
                    {"value": "test", "info": ImportState.DONE, "id": 23},
                    {"value": "new", "info": ImportState.WARNING},
                ],
            },
        }
        assert response.json["results"][0][0]["statistics"][6] == {
            "name": "Committee managers relations",
            "value": 1,
        }

    def test_json_upload_organization_tags(self) -> None:
        self.set_models({"organization_tag/37": {"name": "test"}})
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "committee A",
                        "organization_tags": "test, new",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": "committee A",
                "organization_tags": [
                    {"value": "test", "info": ImportState.DONE, "id": 37},
                    {"value": "new", "info": ImportState.NEW},
                ],
            },
        }
        assert response.json["results"][0][0]["statistics"][0] == {
            "name": "Tags created",
            "value": 1,
        }

    def test_json_upload_forward_to_committees(self) -> None:
        self.set_models({"committee/37": {"name": "test"}})
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "committee A",
                        "forward_to_committees": "test, new",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": "committee A",
                "forward_to_committees": [
                    {"value": "test", "info": ImportState.DONE, "id": 37},
                    {"value": "new", "info": ImportState.NEW},
                ],
            },
        }
        assert response.json["results"][0][0]["statistics"][3] == {
            "name": "Additional committees have been created, because they are mentioned in the forwardings",
            "value": 1,
        }

    def test_json_upload_no_permission(self) -> None:
        self.base_permission_test(
            {}, "committee.json_upload", {"data": [{"name": "test"}]}
        )

    def test_json_upload_permission(self) -> None:
        self.base_permission_test(
            {},
            "committee.json_upload",
            {"data": [{"name": "test"}]},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
