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

    def test_json_upload_date(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "start_date": "2023-08-09",
                        "end_date": "2023-08-10",
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
                "start_date": 1691539200,
                "end_date": 1691625600,
            },
        }

    def test_json_upload_start_date_xor_end_date_error_case(self) -> None:
        """check meeting start_time/end_time condition"""
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "start_date": "2023-08-09",
                    },
                    {
                        "name": "test2",
                        "meeting_name": "test meeting 2",
                        "end_date": "2023-08-10",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.ERROR,
            "messages": [
                "Only one of start_date and end_date is not allowed.",
                "Meeting will be created with meeting.create.",
            ],
            "data": {
                "name": "test",
                "meeting_name": "test meeting",
                "start_date": 1691539200,
            },
        }
        assert response.json["results"][0][0]["rows"][1] == {
            "state": ImportState.ERROR,
            "messages": [
                "Only one of start_date and end_date is not allowed.",
                "Meeting will be created with meeting.create.",
            ],
            "data": {
                "name": "test2",
                "meeting_name": "test meeting 2",
                "end_date": 1691625600,
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
                        "start_date": "2023-08-09",
                        "end_date": "12XX-broken",
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
                        "committee_managers": '"test", "new"',
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": ["Missing committee manager"],
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

    def test_json_upload_committee_managers_wrong_json(self) -> None:
        self.set_models({"user/23": {"username": "test"}})
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "committee A",
                        "committee_managers": "blapzb",
                    }
                ]
            },
        )
        self.assert_status_code(response, 400)
        assert "Could not parse blapzb except string[]" in response.json["message"]

    def test_json_upload_organization_tags(self) -> None:
        self.set_models({"organization_tag/37": {"name": "test"}})
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "committee A",
                        "organization_tags": '"test", "new"',
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
                        "forward_to_committees": '"test", "new"',
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
