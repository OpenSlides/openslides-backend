from typing import Any, Dict

from openslides_backend.action.mixins.import_mixins import ImportState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class BackendImportBaseTest(BaseActionTestCase):
    def assert_row(
        self, row_number: int, row: Dict[str, Any], test_data: Dict[str, Any]
    ) -> None:
        assert test_data["state"] == row.get("state")
        self.assertCountEqual(test_data["messages"], row["messages"])
        row_data = row["data"]
        for key, value in test_data["data"].items():
            try:
                assert value == row_data.get(key)
            except AssertionError as e:
                raise AssertionError(
                    f"data row:{row_number} key:{key} assertion: {str(e)}"
                )


class CommitteeJsonUploadCommittee(BackendImportBaseTest):
    def test_json_upload_create_all_response_correct(self) -> None:
        response = self.request(
            "committee.json_upload",
            {"data": [{"name": "test", "description": "A long text"}]},
        )
        self.assert_status_code(response, 200)
        assert response.json["success"] is True
        assert "Actions handled successfully" in response.json["message"]
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.NEW,
                "messages": [],
                "data": {
                    "name": {"info": "new", "value": "test"},
                    "description": "A long text",
                },
            },
        )
        assert response.json["results"][0][0]["state"] == ImportState.DONE
        assert response.json["results"][0][0]["id"] == 1
        assert response.json["results"][0][0]["headers"] == [
            {"property": "name", "type": "string", "is_object": True},
            {"property": "description", "type": "string"},
            {
                "property": "forward_to_committees",
                "type": "string",
                "is_object": True,
                "is_list": True,
            },
            {
                "property": "organization_tags",
                "type": "string",
                "is_object": True,
                "is_list": True,
            },
            {
                "property": "committee_managers",
                "type": "string",
                "is_object": True,
                "is_list": True,
            },
            {"property": "meeting_name", "type": "string"},
            {"property": "start_time", "type": "date"},
            {"property": "end_time", "type": "date"},
            {
                "property": "meeting_admins",
                "type": "string",
                "is_object": True,
                "is_list": True,
            },
            {"property": "meeting_template", "type": "string", "is_object": True},
        ]
        self.assert_model_exists(
            "action_worker/1",
            {
                "result": {
                    "import": "committee",
                    "rows": [
                        {
                            "state": ImportState.NEW,
                            "messages": [],
                            "data": {
                                "name": {"info": "new", "value": "test"},
                                "description": "A long text",
                            },
                        },
                    ],
                },
            },
        )
        assert response.json["results"][0][0]["statistics"] == [
            {"name": "Row errors", "value": 0},
            {"name": "Committees created", "value": 1},
            {"name": "Committees updated", "value": 0},
            {"name": "Meetings created without template", "value": 0},
            {"name": "Meetings copied from template", "value": 0},
            {"name": "Organization tags created", "value": 0},
        ]

    def test_json_upload_update_correct(self) -> None:
        self.set_models({"committee/7": {"name": "test"}})
        response = self.request("committee.json_upload", {"data": [{"name": "test"}]})
        self.assert_status_code(response, 200)
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.DONE,
                "messages": [],
                "data": {"name": {"info": "done", "value": "test", "id": 7}},
            },
        )

    def test_json_upload_create_duplicate_in_rows(self) -> None:
        """Special case where the same name is in two data entries."""
        response = self.request(
            "committee.json_upload", {"data": [{"name": "n1"}, {"name": "n1"}]}
        )
        self.assert_status_code(response, 200)
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.NEW,
                "messages": [],
                "data": {"name": {"value": "n1", "info": ImportState.NEW}},
            },
        )
        self.assert_row(
            1,
            response.json["results"][0][0]["rows"][1],
            {
                "state": ImportState.NEW,
                "messages": [],
                "data": {"name": {"value": "n1", "info": ImportState.NEW}},
            },
        )

    def test_json_upload_update_duplicate_in_rows_and_db(self) -> None:
        """Special case where the same name is in the db and in two entries."""
        self.set_models({"committee/7": {"name": "n1"}})
        response = self.request(
            "committee.json_upload", {"data": [{"name": "n1"}, {"name": "n1"}]}
        )
        self.assert_status_code(response, 200)
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.DONE,
                "messages": [],
                "data": {"name": {"value": "n1", "info": ImportState.DONE, "id": 7}},
            },
        )
        self.assert_row(
            1,
            response.json["results"][0][0]["rows"][1],
            {
                "state": ImportState.DONE,
                "messages": [],
                "data": {"name": {"value": "n1", "info": ImportState.DONE, "id": 7}},
            },
        )

    def test_json_upload_committee_not_unique_in_db_error(self) -> None:
        self.set_models(
            {"committee/7": {"name": "test"}, "committee/8": {"name": "test"}}
        )
        response = self.request("committee.json_upload", {"data": [{"name": "test"}]})
        self.assert_status_code(response, 200)
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.ERROR,
                "messages": ["Found more committees with the same name in db."],
                "data": {"name": {"value": "test", "info": ImportState.ERROR}},
            },
        )

    def test_json_upload_empty_data_400(self) -> None:
        response = self.request(
            "committee.json_upload",
            {"data": []},
        )
        self.assert_status_code(response, 400)
        assert "data.data must contain at least 1 items" in response.json["message"]


class CommitteeJsonUploadListFields(BackendImportBaseTest):
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
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.NEW,
                "messages": [],
                "data": {
                    "name": {"info": "new", "value": "committee A"},
                    "organization_tags": [
                        {"value": "test", "info": ImportState.NEW, "id": 37},
                        {"value": "new", "info": ImportState.NEW},
                    ],
                },
            },
        )
        assert response.json["results"][0][0]["statistics"] == [
            {"name": "Row errors", "value": 0},
            {"name": "Committees created", "value": 1},
            {"name": "Committees updated", "value": 0},
            {"name": "Meetings created without template", "value": 0},
            {"name": "Meetings copied from template", "value": 0},
            {"name": "Organization tags created", "value": 1},
        ]

    def test_json_upload_organization_tags_update_duplicates(self) -> None:
        """Duplicate tags in same entry and db. Backend removes duplicate"""
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
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.DONE,
                "messages": ["Removed duplicated organization tag(s): [ot1]"],
                "data": {
                    "name": {"value": "n1", "info": ImportState.DONE, "id": 7},
                    "organization_tags": [
                        {"info": ImportState.DONE, "value": "ot1", "id": 8},
                        {"info": ImportState.NEW, "value": "ot2"},
                        {"info": ImportState.WARNING, "value": "ot1"},
                    ],
                },
            },
        )
        assert response.json["results"][0][0]["statistics"] == [
            {"name": "Row errors", "value": 0},
            {"name": "Committees created", "value": 0},
            {"name": "Committees updated", "value": 1},
            {"name": "Meetings created without template", "value": 0},
            {"name": "Meetings copied from template", "value": 0},
            {"name": "Organization tags created", "value": 1},
        ]

    def test_json_upload_committee_managers_remove_all(self) -> None:
        self.set_models(
            {
                "committee/7": {
                    "name": "bar",
                    "user_ids": [4, 5],
                    "manager_ids": [4, 5],
                },
                "user/4": {
                    "username": "bla",
                    "committee_ids": [7],
                    "committee_management_ids": [7],
                },
                "user/5": {
                    "username": "foo",
                    "committee_ids": [7],
                    "committee_management_ids": [7],
                },
            }
        )
        response = self.request(
            "committee.json_upload",
            {"data": [{"name": "bar", "committee_managers": ""}]},
        )
        self.assert_status_code(response, 200)
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.DONE,
                "messages": ["Removed committee manager(s): [bla, foo]"],
                "data": {
                    "name": {"value": "bar", "info": ImportState.DONE, "id": 7},
                    "committee_managers": [],
                },
            },
        )
        assert response.json["results"][0][0]["statistics"] == [
            {"name": "Row errors", "value": 0},
            {"name": "Committees created", "value": 0},
            {"name": "Committees updated", "value": 1},
            {"name": "Meetings created without template", "value": 0},
            {"name": "Meetings copied from template", "value": 0},
            {"name": "Organization tags created", "value": 0},
        ]

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
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.NEW,
                "messages": ["Missing committee manager(s): [new]"],
                "data": {
                    "name": {"value": "committee A", "info": ImportState.NEW},
                    "committee_managers": [
                        {"value": "test", "info": ImportState.NEW, "id": 23},
                        {"value": "new", "info": ImportState.WARNING},
                    ],
                },
            },
        )
        assert response.json["results"][0][0]["statistics"] == [
            {"name": "Row errors", "value": 0},
            {"name": "Committees created", "value": 1},
            {"name": "Committees updated", "value": 0},
            {"name": "Meetings created without template", "value": 0},
            {"name": "Meetings copied from template", "value": 0},
            {"name": "Organization tags created", "value": 0},
        ]

    def test_json_upload_forward_to_committees(self) -> None:
        self.set_models(
            {
                "committee/36": {
                    "name": "committee A",
                    "forward_to_committee_ids": [38],
                },
                "committee/37": {"name": "test"},
                "committee/38": {
                    "name": "should be removed",
                    "receive_forwardings_from_committee_ids": [36],
                },
            }
        )
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "committee A",
                        "forward_to_committees": "test, unknown",
                    }
                ]
            },
        )

        self.assert_status_code(response, 200)
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.DONE,
                "messages": [
                    "Missing forward to committee(s): [unknown]",
                    "Removed forward to committee(s): [should be removed]",
                ],
                "data": {
                    "name": {
                        "value": "committee A",
                        "info": ImportState.DONE,
                        "id": 36,
                    },
                    "forward_to_committees": [
                        {"value": "test", "info": ImportState.NEW, "id": 37},
                        {"value": "unknown", "info": ImportState.WARNING},
                    ],
                },
            },
        )
        assert response.json["results"][0][0]["statistics"] == [
            {"name": "Row errors", "value": 0},
            {"name": "Committees created", "value": 0},
            {"name": "Committees updated", "value": 1},
            {"name": "Meetings created without template", "value": 0},
            {"name": "Meetings copied from template", "value": 0},
            {"name": "Organization tags created", "value": 0},
        ]

    def test_json_upload_forward_to_committees_circular(self) -> None:
        self.set_models(
            {
                "committee/4": {"name": "committee B"},
            }
        )
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "committee A",
                        "forward_to_committees": "committee B,committee C",
                    },
                    {
                        "name": "committee B",
                        "forward_to_committees": "committee C, committee A",
                    },
                    {
                        "name": "committee C",
                        "forward_to_committees": "committee A",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.NEW,
                "messages": [],
                "data": {
                    "name": {"value": "committee A", "info": ImportState.NEW},
                    "forward_to_committees": [
                        {"value": "committee B", "info": ImportState.NEW, "id": 4},
                        {"value": "committee C", "info": ImportState.NEW},
                    ],
                },
            },
        )
        self.assert_row(
            1,
            response.json["results"][0][0]["rows"][1],
            {
                "state": ImportState.DONE,
                "messages": [],
                "data": {
                    "name": {"value": "committee B", "info": ImportState.DONE, "id": 4},
                    "forward_to_committees": [
                        {"value": "committee C", "info": ImportState.NEW},
                        {"value": "committee A", "info": ImportState.NEW},
                    ],
                },
            },
        )
        self.assert_row(
            2,
            response.json["results"][0][0]["rows"][2],
            {
                "state": ImportState.NEW,
                "messages": [],
                "data": {
                    "name": {"value": "committee C", "info": ImportState.NEW},
                    "forward_to_committees": [
                        {"value": "committee A", "info": ImportState.NEW},
                    ],
                },
            },
        )
        assert response.json["results"][0][0]["statistics"] == [
            {"name": "Row errors", "value": 0},
            {"name": "Committees created", "value": 2},
            {"name": "Committees updated", "value": 1},
            {"name": "Meetings created without template", "value": 0},
            {"name": "Meetings copied from template", "value": 0},
            {"name": "Organization tags created", "value": 0},
        ]

    def test_json_upload_update_add_remove_list_fields(self) -> None:
        self.set_models(
            {
                "organization_tag/1": {
                    "name": "ot1",
                    "tagged_ids": ["committee/3", "committee/8"],
                },
                "organization_tag/2": {
                    "name": "ot2",
                    "tagged_ids": ["committee/4", "committee/8"],
                },
                "committee/2": {
                    "name": "c2",
                    "forward_to_committee_ids": [4],
                    "receive_forwardings_from_committee_ids": [8],
                },
                "committee/3": {
                    "name": "c3",
                    "organization_tag_ids": [1],
                    "receive_forwardings_from_committee_ids": [8],
                },
                "committee/4": {
                    "name": "c4",
                    "organization_tag_ids": [2],
                    "receive_forwardings_from_committee_ids": [2],
                },
                "committee/8": {
                    "name": "c8",
                    "organization_tag_ids": [1, 2],
                    "user_ids": [5, 6],
                    "manager_ids": [5, 6],
                    "forward_to_committee_ids": [2, 3],
                },
                "user/5": {
                    "username": "user5",
                    "committee_ids": [8],
                    "committee_management_ids": [8],
                },
                "user/6": {
                    "username": "user6",
                    "committee_ids": [8],
                    "committee_management_ids": [8],
                },
                "user/7": {"username": "user7"},
            }
        )
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "c8",
                        "organization_tags": "ot1, ot3",
                        "committee_managers": "user5, user7, user8",
                        "forward_to_committees": "c3, c4, c5, c9",
                        "meeting_name": "meeting new",
                        "meeting_admins": "user5, user8",
                    },
                    {
                        "name": "c9",
                        "forward_to_committees": "c8",
                        "meeting_name": "",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        row = response.json["results"][0][0]["rows"][0]
        self.assert_row(
            0,
            row,
            {
                "state": ImportState.DONE,
                "messages": [
                    "Missing meeting admin(s): [user8]",
                    "Missing committee manager(s): [user8]",
                    "Removed committee manager(s): [user6]",
                    "Removed organization tag(s): [ot2]",
                    "Missing forward to committee(s): [c5]",
                    "Removed forward to committee(s): [c2]",
                ],
                "data": {
                    "name": {"value": "c8", "info": "done", "id": 8},
                    "organization_tags": [
                        {"value": "ot1", "info": ImportState.DONE, "id": 1},
                        {"value": "ot3", "info": ImportState.NEW},
                    ],
                    "committee_managers": [
                        {"value": "user5", "info": ImportState.DONE, "id": 5},
                        {"value": "user7", "info": ImportState.NEW, "id": 7},
                        {"value": "user8", "info": ImportState.WARNING},
                    ],
                    "forward_to_committees": [
                        {"value": "c3", "info": ImportState.DONE, "id": 3},
                        {"value": "c4", "info": ImportState.NEW, "id": 4},
                        {"value": "c5", "info": ImportState.WARNING},
                        {"value": "c9", "info": ImportState.NEW},
                    ],
                    "meeting_name": "meeting new",
                    "meeting_admins": [
                        {"value": "user5", "info": ImportState.NEW, "id": 5},
                        {"value": "user8", "info": ImportState.WARNING},
                    ],
                    "meeting_template": {"value": None, "info": ImportState.NONE},
                },
            },
        )
        self.assert_row(
            1,
            response.json["results"][0][0]["rows"][1],
            {
                "state": ImportState.NEW,
                "messages": [],
                "data": {
                    "name": {"value": "c9", "info": "new"},
                    "forward_to_committees": [
                        {"value": "c8", "info": ImportState.NEW, "id": 8}
                    ],
                    "meeting_name": "",
                },
            },
        )
        assert response.json["results"][0][0]["statistics"] == [
            {"name": "Row errors", "value": 0},
            {"name": "Committees created", "value": 1},
            {"name": "Committees updated", "value": 1},
            {"name": "Meetings created without template", "value": 1},
            {"name": "Meetings copied from template", "value": 0},
            {"name": "Organization tags created", "value": 1},
        ]


class CommitteeJsonUploadDate(BackendImportBaseTest):
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
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.NEW,
                "messages": [],
                "data": {
                    "name": {"value": "test", "info": ImportState.NEW},
                    "meeting_name": "test meeting",
                    "start_time": 1691539200,
                    "end_time": 1691625600,
                    "meeting_template": {"value": None, "info": ImportState.NONE},
                },
            },
        )

    def test_json_upload_start_time_xor_end_time_error_case(self) -> None:
        """check meeting start_time/end_time condition"""
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_template": "",
                        "start_time": "2023-08-09",
                        "end_time": "",
                    },
                    {
                        "name": "test2",
                        "meeting_name": "test meeting 2",
                        "meeting_template": "",
                        "start_time": "",
                        "end_time": "2023-08-10",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.ERROR,
                "messages": [
                    "Only one of start_time and end_time is not allowed.",
                ],
                "data": {
                    "name": {"value": "test", "info": ImportState.NEW},
                    "meeting_name": "test meeting",
                    "start_time": 1691539200,
                    "end_time": "",
                    "meeting_template": {"info": ImportState.NONE, "value": ""},
                },
            },
        )
        self.assert_row(
            1,
            response.json["results"][0][0]["rows"][1],
            {
                "state": ImportState.ERROR,
                "messages": [
                    "Only one of start_time and end_time is not allowed.",
                ],
                "data": {
                    "name": {"value": "test2", "info": ImportState.NEW},
                    "meeting_name": "test meeting 2",
                    "start_time": "",
                    "end_time": 1691625600,
                    "meeting_template": {"info": ImportState.NONE, "value": ""},
                },
            },
        )

    def test_json_upload_wrong_date(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_template": "",
                        "start_time": "2023-08-09",
                        "end_time": "12XX-broken",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.ERROR,
                "messages": [
                    "Could not parse end_time 12XX-broken: expected date",
                ],
                "data": {
                    "name": {"value": "test", "info": ImportState.NEW},
                    "meeting_name": "test meeting",
                    "start_time": 1691539200,
                    "end_time": "12XX-broken",
                    "meeting_template": {"info": ImportState.NONE, "value": ""},
                },
            },
        )

    def test_json_upload_start_date_after_end_date(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_template": "",
                        "start_time": "2023-08-10",
                        "end_time": "2023-08-09",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.ERROR,
                "messages": [
                    "Start time may not be after end time.",
                ],
                "data": {
                    "name": {"value": "test", "info": ImportState.NEW},
                    "meeting_name": "test meeting",
                    "start_time": 1691625600,
                    "end_time": 1691539200,
                    "meeting_template": {
                        "info": ImportState.NONE,
                        "value": "",
                    },
                },
            },
        )
        assert response.json["results"][0][0]["statistics"] == [
            {"name": "Row errors", "value": 1},
            {"name": "Committees created", "value": 0},
            {"name": "Committees updated", "value": 0},
            {"name": "Meetings created without template", "value": 0},
            {"name": "Meetings copied from template", "value": 0},
            {"name": "Organization tags created", "value": 0},
        ]


class CommitteeJsonUploadMeeting(BackendImportBaseTest):
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
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.NEW,
                "messages": ["No meeting will be created without meeting_name"],
                "data": {
                    "name": {"value": "test", "info": ImportState.NEW},
                    "meeting_template": "testtemplate",
                },
            },
        )
        assert response.json["results"][0][0]["statistics"] == [
            {"name": "Row errors", "value": 0},
            {"name": "Committees created", "value": 1},
            {"name": "Committees updated", "value": 0},
            {"name": "Meetings created without template", "value": 0},
            {"name": "Meetings copied from template", "value": 0},
            {"name": "Organization tags created", "value": 0},
        ]

    def test_json_upload_meeting_create(self) -> None:
        self.set_models({"meeting/23": {"name": "test"}})
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_template": "",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.NEW,
                "messages": [],
                "data": {
                    "name": {"value": "test", "info": ImportState.NEW},
                    "meeting_name": "test meeting",
                    "meeting_template": {
                        "value": "",
                        "info": ImportState.NONE,
                    },
                },
            },
        )
        assert response.json["results"][0][0]["statistics"] == [
            {"name": "Row errors", "value": 0},
            {"name": "Committees created", "value": 1},
            {"name": "Committees updated", "value": 0},
            {"name": "Meetings created without template", "value": 1},
            {"name": "Meetings copied from template", "value": 0},
            {"name": "Organization tags created", "value": 0},
        ]

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
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.NEW,
                "messages": ["Meeting will be created with meeting.create."],
                "data": {
                    "name": {"value": "test", "info": ImportState.NEW},
                    "meeting_name": "test meeting",
                    "meeting_template": {"value": "test", "info": ImportState.WARNING},
                },
            },
        )
        assert response.json["results"][0][0]["statistics"] == [
            {"name": "Row errors", "value": 0},
            {"name": "Committees created", "value": 1},
            {"name": "Committees updated", "value": 0},
            {"name": "Meetings created without template", "value": 1},
            {"name": "Meetings copied from template", "value": 0},
            {"name": "Organization tags created", "value": 0},
        ]

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
        self.assert_row(
            0,
            response.json["results"][0][0]["rows"][0],
            {
                "state": ImportState.NEW,
                "messages": [],
                "data": {
                    "name": {"value": "test", "info": ImportState.NEW},
                    "meeting_name": "test meeting",
                    "meeting_template": {
                        "value": "test",
                        "info": ImportState.DONE,
                        "id": 23,
                    },
                },
            },
        )
        assert response.json["results"][0][0]["statistics"] == [
            {"name": "Row errors", "value": 0},
            {"name": "Committees created", "value": 1},
            {"name": "Committees updated", "value": 0},
            {"name": "Meetings created without template", "value": 0},
            {"name": "Meetings copied from template", "value": 1},
            {"name": "Organization tags created", "value": 0},
        ]


class CommitteeJsonUploadPermission(BackendImportBaseTest):
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
