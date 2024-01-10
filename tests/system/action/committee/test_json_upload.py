from math import ceil, floor
from time import time
from typing import Any, Dict

from openslides_backend.action.mixins.import_mixins import ImportState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase
from tests.util import Response


class CommitteeJsonUploadCommittee(BaseActionTestCase):
    def get_row(self, response: Response, index: int = 0) -> Dict[str, Any]:
        return response.json["results"][0][0]["rows"][index]

    def test_json_upload_minimal_fields(self) -> None:
        start = floor(time())
        response = self.request(
            "committee.json_upload",
            {"data": [{"name": "test"}]},
        )
        end = ceil(time())
        self.assert_status_code(response, 200)
        assert response.json["success"] is True
        assert "Actions handled successfully" in response.json["message"]
        assert response.json["results"][0][0] == {
            "rows": [
                {
                    "state": ImportState.NEW,
                    "messages": [],
                    "data": {
                        "name": {"info": "new", "value": "test"},
                    },
                }
            ],
            "state": ImportState.DONE,
            "id": 1,
            "headers": [
                {"property": "name", "type": "string"},
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
                    "property": "managers",
                    "type": "string",
                    "is_object": True,
                    "is_list": True,
                },
                {"property": "meeting_name", "type": "string"},
                {"property": "meeting_start_time", "type": "date"},
                {"property": "meeting_end_time", "type": "date"},
                {
                    "property": "meeting_admins",
                    "type": "string",
                    "is_object": True,
                    "is_list": True,
                },
                {"property": "meeting_template", "type": "string", "is_object": True},
            ],
            "statistics": [
                {"name": "total", "value": 1},
                {"name": "created", "value": 1},
                {"name": "updated", "value": 0},
                {"name": "error", "value": 0},
                {"name": "warning", "value": 0},
            ],
        }
        import_preview = self.assert_model_exists(
            "import_preview/1", {"name": "committee", "state": ImportState.DONE}
        )
        assert start <= import_preview["created"] <= end

    def test_json_upload_update_correct(self) -> None:
        self.set_models({"committee/7": {"name": "test"}})
        response = self.request("committee.json_upload", {"data": [{"name": "test"}]})
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.DONE,
            "messages": [],
            "data": {"name": {"info": "done", "value": "test", "id": 7}},
        }

    def test_json_upload_duplicate_in_rows(self) -> None:
        response = self.request(
            "committee.json_upload", {"data": [{"name": "n1"}, {"name": "n1"}]}
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response, 0) == {
            "state": ImportState.ERROR,
            "messages": ["Found multiple committees with the same name."],
            "data": {"name": {"value": "n1", "info": ImportState.ERROR}},
        }
        assert self.get_row(response, 1) == {
            "state": ImportState.ERROR,
            "messages": ["Found multiple committees with the same name."],
            "data": {"name": {"value": "n1", "info": ImportState.ERROR}},
        }

    def test_json_upload_duplicate_in_rows_and_db(self) -> None:
        self.set_models({"committee/7": {"name": "n1"}})
        response = self.request(
            "committee.json_upload", {"data": [{"name": "n1"}, {"name": "n1"}]}
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response, 0) == {
            "state": ImportState.ERROR,
            "messages": ["Found multiple committees with the same name."],
            "data": {"name": {"value": "n1", "info": ImportState.ERROR}},
        }
        assert self.get_row(response, 1) == {
            "state": ImportState.ERROR,
            "messages": ["Found multiple committees with the same name."],
            "data": {"name": {"value": "n1", "info": ImportState.ERROR}},
        }

    def test_json_upload_committee_not_unique_in_db(self) -> None:
        self.set_models(
            {"committee/7": {"name": "test"}, "committee/8": {"name": "test"}}
        )
        response = self.request("committee.json_upload", {"data": [{"name": "test"}]})
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.ERROR,
            "messages": ["Found multiple committees with the same name."],
            "data": {"name": {"value": "test", "info": ImportState.ERROR}},
        }

    def test_json_upload_empty_data(self) -> None:
        response = self.request(
            "committee.json_upload",
            {"data": []},
        )
        self.assert_status_code(response, 400)
        assert "data.data must contain at least 1 items" in response.json["message"]

    def test_json_upload_missing_name(self) -> None:
        response = self.request(
            "committee.json_upload",
            {"data": [{}]},
        )
        self.assert_status_code(response, 400)
        assert (
            "data.data[0] must contain ['name'] properties" in response.json["message"]
        )

    def test_json_upload_organization_tags(self) -> None:
        self.set_models({"organization_tag/37": {"name": "test"}})
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "committee A",
                        "organization_tags": ["test", "new"],
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": {"info": ImportState.NEW, "value": "committee A"},
                "organization_tags": [
                    {"value": "test", "info": ImportState.DONE, "id": 37},
                    {"value": "new", "info": ImportState.NEW},
                ],
            },
        }

    def test_json_upload_organization_tags_update_duplicates(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {"name": "n1", "organization_tags": ["ot1", "ot2", "ot1"]},
                ]
            },
        )
        self.assert_status_code(response, 400)
        assert "organization_tags must contain unique items" in response.json["message"]

    def test_json_upload_managers(self) -> None:
        response = self.request(
            "committee.json_upload",
            {"data": [{"name": "test", "managers": ["admin", "missing"]}]},
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.NEW,
            "messages": ["Following values of managers were not found: 'missing'"],
            "data": {
                "name": {"value": "test", "info": ImportState.NEW},
                "managers": [
                    {"value": "admin", "info": ImportState.DONE, "id": 1},
                    {"value": "missing", "info": ImportState.WARNING},
                ],
            },
        }

    def test_json_upload_forward_to_committees(self) -> None:
        self.set_models(
            {
                "committee/37": {"name": "test"},
            }
        )
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "committee A",
                        "forward_to_committees": ["test", "committee B", "missing"],
                    },
                    {
                        "name": "committee B",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.NEW,
            "messages": [
                "Following values of forward_to_committees were not found: 'missing'",
            ],
            "data": {
                "name": {
                    "value": "committee A",
                    "info": ImportState.NEW,
                },
                "forward_to_committees": [
                    {"value": "test", "info": ImportState.DONE, "id": 37},
                    {"value": "committee B", "info": ImportState.DONE},
                    {"value": "missing", "info": ImportState.WARNING},
                ],
            },
        }

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
                        "forward_to_committees": ["committee B", "committee C"],
                    },
                    {
                        "name": "committee B",
                        "forward_to_committees": ["committee C", "committee A"],
                    },
                    {
                        "name": "committee C",
                        "forward_to_committees": ["committee A"],
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response, 0) == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": {"value": "committee A", "info": ImportState.NEW},
                "forward_to_committees": [
                    {"value": "committee B", "info": ImportState.DONE, "id": 4},
                    {"value": "committee C", "info": ImportState.DONE},
                ],
            },
        }
        assert self.get_row(response, 1) == {
            "state": ImportState.DONE,
            "messages": [],
            "data": {
                "name": {"value": "committee B", "info": ImportState.DONE, "id": 4},
                "forward_to_committees": [
                    {"value": "committee C", "info": ImportState.DONE},
                    {"value": "committee A", "info": ImportState.DONE},
                ],
            },
        }
        assert self.get_row(response, 2) == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": {"value": "committee C", "info": ImportState.NEW},
                "forward_to_committees": [
                    {"value": "committee A", "info": ImportState.DONE},
                ],
            },
        }

    def test_json_upload_with_meeting_name(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": {"value": "test", "info": ImportState.NEW},
                "meeting_name": "test meeting",
            },
        }

    def test_json_upload_with_dates(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_start_time": "2023-08-09",
                        "meeting_end_time": "2023-08-10",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": {"value": "test", "info": ImportState.NEW},
                "meeting_name": "test meeting",
                "meeting_start_time": 1691539200,
                "meeting_end_time": 1691625600,
            },
        }

    def test_json_upload_duplicate_meeting(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "committee", "meeting_ids": [2]},
                "meeting/2": {
                    "name": "meeting",
                    "committee_id": 1,
                    "start_time": 1691582400,
                    "end_time": 1691668800,
                },
            }
        )
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "committee",
                        "meeting_name": "meeting",
                        "meeting_start_time": "2023-08-09",
                        "meeting_end_time": "2023-08-10",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.ERROR,
            "messages": ["A meeting with this name and dates already exists."],
            "data": {
                "name": {"value": "committee", "info": ImportState.DONE, "id": 1},
                "meeting_name": "meeting",
                "meeting_start_time": 1691539200,
                "meeting_end_time": 1691625600,
            },
        }

    def test_json_upload_missing_start_or_end_time(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_start_time": "2023-08-09",
                    },
                    {
                        "name": "test2",
                        "meeting_name": "test meeting 2",
                        "meeting_end_time": "2023-08-10",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response, 0) == {
            "state": ImportState.ERROR,
            "messages": [
                "Only one of start_time and end_time is not allowed.",
            ],
            "data": {
                "name": {"value": "test", "info": ImportState.NEW},
                "meeting_name": "test meeting",
                "meeting_start_time": 1691539200,
            },
        }
        assert self.get_row(response, 1) == {
            "state": ImportState.ERROR,
            "messages": [
                "Only one of start_time and end_time is not allowed.",
            ],
            "data": {
                "name": {"value": "test2", "info": ImportState.NEW},
                "meeting_name": "test meeting 2",
                "meeting_end_time": 1691625600,
            },
        }

    def test_json_upload_invalid_date(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_template": "",
                        "meeting_start_time": "2023-08-09",
                        "meeting_end_time": "12XX-broken",
                    }
                ]
            },
        )
        self.assert_status_code(response, 400)
        assert "Invalid date format" in response.json["message"]

    def test_json_upload_start_date_after_end_date(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_start_time": "2023-08-10",
                        "meeting_end_time": "2023-08-09",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.ERROR,
            "messages": [
                "start_time must be before end_time.",
            ],
            "data": {
                "name": {"value": "test", "info": ImportState.NEW},
                "meeting_name": "test meeting",
                "meeting_start_time": 1691625600,
                "meeting_end_time": 1691539200,
            },
        }

    def test_json_upload_meeting_field_without_meeting_name(self) -> None:
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
        assert self.get_row(response) == {
            "state": ImportState.NEW,
            "messages": [
                "No meeting will be created without meeting_name",
                "Template meetings can only be used for existing committees.",
            ],
            "data": {
                "name": {"value": "test", "info": ImportState.NEW},
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
        assert self.get_row(response) == {
            "state": ImportState.NEW,
            "messages": ["Template meetings can only be used for existing committees."],
            "data": {
                "name": {"value": "test", "info": ImportState.NEW},
                "meeting_name": "test meeting",
                "meeting_template": {"value": "test", "info": ImportState.WARNING},
            },
        }

    def test_json_upload_meeting_template_found(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "committee", "meeting_ids": [2]},
                "meeting/2": {"name": "template", "committee_id": 1},
            }
        )
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "committee",
                        "meeting_name": "test",
                        "meeting_template": "template",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.DONE,
            "messages": [],
            "data": {
                "name": {"value": "committee", "info": ImportState.DONE, "id": 1},
                "meeting_name": "test",
                "meeting_template": {
                    "value": "template",
                    "info": ImportState.DONE,
                    "id": 2,
                },
            },
        }

    def test_json_upload_meeting_template_in_another_committee(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "committee1", "meeting_ids": [2]},
                "committee/2": {"name": "committee2"},
                "meeting/2": {"name": "template", "committee_id": 1},
            }
        )
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "committee2",
                        "meeting_name": "test",
                        "meeting_template": "template",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.DONE,
            "messages": [
                "The meeting template template was not found, the meeting will be created without a template."
            ],
            "data": {
                "name": {"value": "committee2", "info": ImportState.DONE, "id": 2},
                "meeting_name": "test",
                "meeting_template": {
                    "value": "template",
                    "info": ImportState.WARNING,
                },
            },
        }

    def test_json_upload_meeting_admins(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_admins": ["admin", "missing"],
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.NEW,
            "messages": [
                "Following values of meeting_admins were not found: 'missing'"
            ],
            "data": {
                "name": {"value": "test", "info": ImportState.NEW},
                "meeting_name": "test meeting",
                "meeting_admins": [
                    {
                        "value": "admin",
                        "info": ImportState.DONE,
                        "id": 1,
                    },
                    {
                        "value": "missing",
                        "info": ImportState.WARNING,
                    },
                ],
            },
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
