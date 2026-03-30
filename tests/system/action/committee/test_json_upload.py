from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from openslides_backend.action.mixins.import_mixins import ImportState, StatisticEntry
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase
from tests.system.base import ADMIN_USERNAME
from tests.util import Response


class BaseCommitteeJsonUploadTest(BaseActionTestCase):
    def get_row(self, response: Response, index: int = 0) -> dict[str, Any]:
        return response.json["results"][0][0]["rows"][index]

    def get_statistics(self, response: Response) -> list[StatisticEntry]:
        return response.json["results"][0][0]["statistics"]

    def assert_statistics(self, response: Response, expected: dict[str, int]) -> None:
        for key, value in expected.items():
            self.assertIn({"name": key, "value": value}, self.get_statistics(response))


class TestCommitteeJsonUpload(BaseCommitteeJsonUploadTest):
    def test_json_upload_minimal_fields(self) -> None:
        start = datetime.now(ZoneInfo("UTC"))
        response = self.request(
            "committee.json_upload",
            {"data": [{"name": "test"}]},
        )
        end = datetime.now(ZoneInfo("UTC"))
        self.assert_status_code(response, 200)
        assert response.json["success"] is True
        assert "Actions handled successfully" in response.json["message"]
        assert response.json["results"][0][0] == {
            "rows": [
                {
                    "state": ImportState.NEW,
                    "messages": [],
                    "data": {
                        "name": {"info": ImportState.NEW, "value": "test"},
                    },
                }
            ],
            "state": ImportState.DONE,
            "id": 1,
            "headers": [
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
                    "property": "managers",
                    "type": "string",
                    "is_object": True,
                    "is_list": True,
                },
                {"property": "meeting_name", "type": "string"},
                {"property": "meeting_start_time", "type": "date"},
                {"property": "meeting_end_time", "type": "date"},
                {"property": "meeting_time_zone", "type": "string", "is_object": True},
                {
                    "property": "meeting_admins",
                    "type": "string",
                    "is_object": True,
                    "is_list": True,
                },
                {"property": "meeting_template", "type": "string", "is_object": True},
                {"property": "parent", "type": "string", "is_object": True},
            ],
            "statistics": [
                {"name": "total", "value": 1},
                {"name": "created", "value": 1},
                {"name": "updated", "value": 0},
                {"name": "error", "value": 0},
                {"name": "warning", "value": 0},
                {"name": "meetings_created", "value": 0},
                {"name": "meetings_cloned", "value": 0},
                {"name": "organization_tags_created", "value": 0},
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
            "data": {"id": 7, "name": {"info": "done", "value": "test", "id": 7}},
        }
        assert self.get_statistics(response) == [
            {"name": "total", "value": 1},
            {"name": "created", "value": 0},
            {"name": "updated", "value": 1},
            {"name": "error", "value": 0},
            {"name": "warning", "value": 0},
            {"name": "meetings_created", "value": 0},
            {"name": "meetings_cloned", "value": 0},
            {"name": "organization_tags_created", "value": 0},
        ]

    def test_json_upload_duplicate_in_rows(self) -> None:
        response = self.request(
            "committee.json_upload", {"data": [{"name": "n1"}, {"name": "n1"}]}
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response, 0) == {
            "state": ImportState.ERROR,
            "messages": ["Error: Found multiple committees with the same name."],
            "data": {"name": {"value": "n1", "info": ImportState.ERROR}},
        }
        assert self.get_row(response, 1) == {
            "state": ImportState.ERROR,
            "messages": ["Error: Found multiple committees with the same name."],
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
            "messages": ["Error: Found multiple committees with the same name."],
            "data": {"name": {"value": "n1", "info": ImportState.ERROR}},
        }
        assert self.get_row(response, 1) == {
            "state": ImportState.ERROR,
            "messages": ["Error: Found multiple committees with the same name."],
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
            "messages": ["Error: Found multiple committees with the same name."],
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
        self.set_models({"organization_tag/37": {"name": "test", "color": "#FFFF00"}})
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
        self.assert_statistics(response, {"organization_tags_created": 1})

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
                "id": 4,
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

    def test_json_upload_with_meeting_name_no_admin(self) -> None:
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
            "state": ImportState.ERROR,
            "messages": ["Error: Meeting cannot be created without admins"],
            "data": {
                "name": {"value": "test", "info": ImportState.NEW},
                "meeting_name": "test meeting",
                "meeting_admins": [{"value": "", "info": ImportState.ERROR}],
            },
        }
        self.assert_statistics(response, {"meetings_created": 0, "error": 1})

    def test_json_upload_with_meeting_name_and_admin(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_admins": [ADMIN_USERNAME],
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
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
            },
        }
        self.assert_statistics(response, {"meetings_created": 1})

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
                        "meeting_admins": [ADMIN_USERNAME],
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.NEW,
            "messages": [
                "Since no timezone was given, the dates will be interpreted as being in the 'UTC' zone."
            ],
            "data": {
                "name": {"value": "test", "info": ImportState.NEW},
                "meeting_name": "test meeting",
                "meeting_start_time": 1691539200,
                "meeting_end_time": 1691625600,
                "meeting_time_zone": {"info": ImportState.WARNING, "value": None},
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
            },
        }

    def test_json_upload_with_dates_and_timezone(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_start_time": "2023-08-09",
                        "meeting_end_time": "2023-08-10",
                        "meeting_time_zone": "Europe/Vatican",
                        "meeting_admins": [ADMIN_USERNAME],
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
                # time offset +2hrs in rome during dst
                "meeting_start_time": 1691539200 - 2 * 3600,
                "meeting_end_time": 1691625600 - 2 * 3600,
                "meeting_time_zone": {
                    "info": ImportState.DONE,
                    "value": "Europe/Vatican",
                },
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
            },
        }

    def test_json_upload_with_dates_and_non_mean_timezone(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_start_time": "2023-08-09",
                        "meeting_end_time": "2023-08-10",
                        "meeting_time_zone": "Asia/Pyongyang",
                        "meeting_admins": [ADMIN_USERNAME],
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
                # Time offset +9hrs in pyongyang
                "meeting_start_time": 1691539200 - 9 * 3600,
                "meeting_end_time": 1691625600 - 9 * 3600,
                "meeting_time_zone": {
                    "info": ImportState.DONE,
                    "value": "Asia/Pyongyang",
                },
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
            },
        }

    def test_json_upload_with_dates_and_invalid_timezone(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_start_time": "2023-08-09",
                        "meeting_end_time": "2023-08-10",
                        "meeting_time_zone": "Mars/Acidalia_Planitia",
                        "meeting_admins": [ADMIN_USERNAME],
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.ERROR,
            "messages": [
                "Error: Invalid timezone format: Mars/Acidalia_Planitia (expected canonic IANA timezone name)"
            ],
            "data": {
                "name": {"value": "test", "info": ImportState.NEW},
                "meeting_name": "test meeting",
                "meeting_start_time": 1691539200,
                "meeting_end_time": 1691625600,
                "meeting_time_zone": {
                    "info": ImportState.ERROR,
                    "value": "Mars/Acidalia_Planitia",
                },
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
            },
        }

    def test_json_upload_duplicate_meeting(self) -> None:
        self.create_meeting(
            2,
            {
                "name": "meeting",
                "start_time": datetime.fromtimestamp(1691582400),
                "end_time": datetime.fromtimestamp(1691668800),
            },
        )
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "Committee61",
                        "meeting_name": "meeting",
                        "meeting_start_time": "2023-08-09",
                        "meeting_end_time": "2023-08-10",
                        "meeting_admins": [ADMIN_USERNAME],
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.ERROR,
            "messages": [
                "Since no timezone was given, the dates will be interpreted as being in the 'UTC' zone.",
                "Error: A meeting with this name and dates already exists.",
            ],
            "data": {
                "id": 61,
                "name": {"value": "Committee61", "info": ImportState.DONE, "id": 61},
                "meeting_name": "meeting",
                "meeting_start_time": 1691539200,
                "meeting_end_time": 1691625600,
                "meeting_time_zone": {"info": ImportState.WARNING, "value": None},
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
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
                        "meeting_admins": [ADMIN_USERNAME],
                    },
                    {
                        "name": "test2",
                        "meeting_name": "test meeting 2",
                        "meeting_end_time": "2023-08-10",
                        "meeting_admins": [ADMIN_USERNAME],
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response, 0) == {
            "state": ImportState.ERROR,
            "messages": [
                "Since no timezone was given, the dates will be interpreted as being in the 'UTC' zone.",
                "Error: Only one of start_time and end_time is not allowed.",
            ],
            "data": {
                "name": {"value": "test", "info": ImportState.NEW},
                "meeting_name": "test meeting",
                "meeting_start_time": 1691539200,
                "meeting_time_zone": {"info": ImportState.WARNING, "value": None},
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
            },
        }
        assert self.get_row(response, 1) == {
            "state": ImportState.ERROR,
            "messages": [
                "Since no timezone was given, the dates will be interpreted as being in the 'UTC' zone.",
                "Error: Only one of start_time and end_time is not allowed.",
            ],
            "data": {
                "name": {"value": "test2", "info": ImportState.NEW},
                "meeting_name": "test meeting 2",
                "meeting_end_time": 1691625600,
                "meeting_time_zone": {"info": ImportState.WARNING, "value": None},
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
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
        self.set_models({"organization/1": {"time_zone": "Europe/Chisinau"}})
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_start_time": "2023-08-10",
                        "meeting_end_time": "2023-08-09",
                        "meeting_admins": [ADMIN_USERNAME],
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.ERROR,
            "messages": [
                "Since no timezone was given, the dates will be interpreted as being in the 'Europe/Chisinau' zone.",
                "Error: start_time must be before end_time.",
            ],
            "data": {
                "name": {"value": "test", "info": ImportState.NEW},
                "meeting_name": "test meeting",
                # Moldova is +3hrs during DST
                "meeting_start_time": 1691625600 - (3 * 3600),
                "meeting_end_time": 1691539200 - (3 * 3600),
                "meeting_time_zone": {"info": ImportState.WARNING, "value": None},
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
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
        self.assert_statistics(response, {"meetings_created": 0, "meetings_cloned": 0})

    def test_json_upload_meeting_template_found_but_no_admin(self) -> None:
        self.create_meeting(2, {"name": "template"})
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "Committee61",
                        "meeting_name": "test",
                        "meeting_template": "template",
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.ERROR,
            "messages": ["Error: Meeting cannot be created without admins"],
            "data": {
                "id": 61,
                "name": {"value": "Committee61", "info": ImportState.DONE, "id": 61},
                "meeting_name": "test",
                "meeting_template": {
                    "value": "template",
                    "info": ImportState.DONE,
                    "id": 2,
                },
                "meeting_admins": [{"value": "", "info": ImportState.ERROR}],
            },
        }
        self.assert_statistics(
            response, {"meetings_created": 0, "meetings_cloned": 0, "error": 1}
        )

    def test_json_upload_meeting_template_in_another_committee(self) -> None:
        self.create_meeting(2, {"name": "template"})
        self.set_models({"committee/62": {"name": "committee62"}})
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "committee62",
                        "meeting_name": "test",
                        "meeting_template": "template",
                        "meeting_admins": [ADMIN_USERNAME],
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
                "id": 62,
                "name": {"value": "committee62", "info": ImportState.DONE, "id": 62},
                "meeting_name": "test",
                "meeting_template": {
                    "value": "template",
                    "info": ImportState.WARNING,
                },
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
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

    def create_committees_for_parent_tests(self) -> None:
        self.create_committee(name="National council")
        self.create_committee(2, name="Regional council")
        self.create_committee(3, parent_id=2, name="County council")
        self.create_committee(4, parent_id=3, name="District council")

    def test_json_upload_parent_circle(self) -> None:
        self.create_committees_for_parent_tests()
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "National conference",
                        "parent": "National council",
                    },
                    {
                        "name": "Parliamentary committee",
                        "parent": "Landscaping committee",
                    },
                    {
                        "name": "Financing committee",
                        "parent": "Parliamentary committee",
                    },
                    {
                        "name": "Landscaping committee",
                        "parent": "Financing committee",
                    },
                    {
                        "name": "Pond building committee",
                        "parent": "Landscaping committee",
                    },
                    {"name": "Unrelated committee"},
                    {
                        "name": "Unrelated child committee",
                        "parent": "Unrelated committee",
                    },
                    {"name": "Regional council", "parent": "District council"},
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.ERROR
        assert self.get_row(response) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "National conference",
                },
                "parent": {
                    "id": 1,
                    "info": ImportState.DONE,
                    "value": "National council",
                },
            },
            "messages": [],
            "state": ImportState.NEW,
        }
        assert self.get_row(response, 1) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "Parliamentary committee",
                },
                "parent": {
                    "info": ImportState.ERROR,
                    "value": "Landscaping committee",
                },
            },
            "messages": [
                "Error: The parents are forming circles, please rework the hierarchy"
            ],
            "state": ImportState.ERROR,
        }
        assert self.get_row(response, 2) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "Financing committee",
                },
                "parent": {
                    "info": ImportState.ERROR,
                    "value": "Parliamentary committee",
                },
            },
            "messages": [
                "Error: The parents are forming circles, please rework the hierarchy"
            ],
            "state": ImportState.ERROR,
        }
        assert self.get_row(response, 3) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "Landscaping committee",
                },
                "parent": {
                    "info": ImportState.ERROR,
                    "value": "Financing committee",
                },
            },
            "messages": [
                "Error: The parents are forming circles, please rework the hierarchy"
            ],
            "state": ImportState.ERROR,
        }
        assert self.get_row(response, 4) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "Pond building committee",
                },
                "parent": {
                    "info": ImportState.NEW,
                    "value": "Landscaping committee",
                },
            },
            "messages": [],
            "state": ImportState.NEW,
        }
        assert self.get_row(response, 5) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "Unrelated committee",
                },
            },
            "messages": [],
            "state": ImportState.NEW,
        }
        assert self.get_row(response, 6) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "Unrelated child committee",
                },
                "parent": {
                    "info": ImportState.NEW,
                    "value": "Unrelated committee",
                },
            },
            "messages": [],
            "state": ImportState.NEW,
        }
        assert self.get_row(response, 7) == {
            "data": {
                "id": 2,
                "name": {
                    "id": 2,
                    "info": ImportState.DONE,
                    "value": "Regional council",
                },
                "parent": {
                    "info": ImportState.ERROR,
                    "value": "District council",
                },
            },
            "messages": [
                "Error: The parents are forming circles, please rework the hierarchy"
            ],
            "state": ImportState.ERROR,
        }

    def test_json_upload_multiple_circles(self) -> None:
        self.create_committees_for_parent_tests()
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "Parliamentary committee",
                        "parent": "Landscaping committee",
                    },
                    {
                        "name": "Financing committee",
                        "parent": "Parliamentary committee",
                    },
                    {
                        "name": "Landscaping committee",
                        "parent": "Financing committee",
                    },
                    {
                        "name": "Unrelated committee",
                        "parent": "Unrelated child committee",
                    },
                    {
                        "name": "Unrelated child committee",
                        "parent": "Unrelated committee",
                    },
                    {
                        "name": "Recursion committee",
                        "parent": "Recursion committee",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.ERROR
        assert self.get_row(response) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "Parliamentary committee",
                },
                "parent": {
                    "info": ImportState.ERROR,
                    "value": "Landscaping committee",
                },
            },
            "messages": [
                "Error: The parents are forming circles, please rework the hierarchy",
            ],
            "state": ImportState.ERROR,
        }
        assert self.get_row(response, 1) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "Financing committee",
                },
                "parent": {
                    "info": ImportState.ERROR,
                    "value": "Parliamentary committee",
                },
            },
            "messages": [
                "Error: The parents are forming circles, please rework the hierarchy",
            ],
            "state": ImportState.ERROR,
        }
        assert self.get_row(response, 2) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "Landscaping committee",
                },
                "parent": {
                    "info": ImportState.ERROR,
                    "value": "Financing committee",
                },
            },
            "messages": [
                "Error: The parents are forming circles, please rework the hierarchy",
            ],
            "state": ImportState.ERROR,
        }
        assert self.get_row(response, 3) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "Unrelated committee",
                },
                "parent": {
                    "info": ImportState.ERROR,
                    "value": "Unrelated child committee",
                },
            },
            "messages": [
                "Error: The parents are forming circles, please rework the hierarchy",
            ],
            "state": ImportState.ERROR,
        }
        assert self.get_row(response, 4) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "Unrelated child committee",
                },
                "parent": {
                    "info": ImportState.ERROR,
                    "value": "Unrelated committee",
                },
            },
            "messages": [
                "Error: The parents are forming circles, please rework the hierarchy",
            ],
            "state": ImportState.ERROR,
        }
        assert self.get_row(response, 5) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "Recursion committee",
                },
                "parent": {
                    "info": ImportState.ERROR,
                    "value": "Recursion committee",
                },
            },
            "messages": [
                "Error: The parents are forming circles, please rework the hierarchy",
            ],
            "state": ImportState.ERROR,
        }


class TestCommitteeJsonUploadForImport(BaseCommitteeJsonUploadTest):
    def json_upload_all_fields(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "forward"},
                "user/2": {"username": "meeting_admin"},
            }
        )
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "description": "desc",
                        "forward_to_committees": ["forward"],
                        "organization_tags": ["tag"],
                        "managers": ["admin"],
                        "meeting_name": "meeting",
                        "meeting_start_time": "2023-08-09",
                        "meeting_end_time": "2023-08-10",
                        "meeting_time_zone": "Atlantic/Azores",
                        "meeting_admins": ["meeting_admin"],
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": {"info": ImportState.NEW, "value": "test"},
                "description": "desc",
                "forward_to_committees": [
                    {"value": "forward", "info": ImportState.DONE, "id": 1}
                ],
                "organization_tags": [{"value": "tag", "info": ImportState.NEW}],
                "managers": [{"value": "admin", "info": ImportState.DONE, "id": 1}],
                "meeting_name": "meeting",
                "meeting_start_time": 1691539200,
                "meeting_end_time": 1691625600,
                "meeting_time_zone": {
                    "info": ImportState.DONE,
                    "value": "Atlantic/Azores",
                },
                "meeting_admins": [
                    {"value": "meeting_admin", "info": ImportState.DONE, "id": 2}
                ],
            },
        }

    def json_upload_with_timestamps_orga_timezone(self) -> None:
        self.set_models({"organization/1": {"time_zone": "Australia/Lord_Howe"}})
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "A weird place",
                        "description": "Lord Howe Island has 30min DST transition.",
                        "managers": ["admin"],
                        "meeting_name": "Lord Howe Meeting",
                        "meeting_start_time": "2027-01-01",
                        "meeting_end_time": "2027-07-01",
                        "meeting_admins": ["admin"],
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.NEW,
            "messages": [
                "Since no timezone was given, the dates will be interpreted as being in the 'Australia/Lord_Howe' zone."
            ],
            "data": {
                "name": {"info": ImportState.NEW, "value": "A weird place"},
                "description": "Lord Howe Island has 30min DST transition.",
                "managers": [{"value": "admin", "info": ImportState.DONE, "id": 1}],
                "meeting_name": "Lord Howe Meeting",
                "meeting_start_time": 1798761600 - 11 * 3600,
                "meeting_end_time": 1814400000 - 10 * 3600 - 1800,
                "meeting_time_zone": {"info": ImportState.WARNING, "value": None},
                "meeting_admins": [
                    {"value": "admin", "info": ImportState.DONE, "id": 1}
                ],
            },
        }

    def json_upload_with_timestamps_no_timezone(self) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "Armageddon",
                        "description": "It's the end of the world as we know it.",
                        "managers": ["admin"],
                        "meeting_name": "Armageddon Countdown",
                        "meeting_start_time": "2012-12-21",
                        "meeting_end_time": "2012-12-21",
                        "meeting_admins": ["admin"],
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.NEW,
            "messages": [
                "Since no timezone was given, the dates will be interpreted as being in the 'UTC' zone."
            ],
            "data": {
                "name": {"info": ImportState.NEW, "value": "Armageddon"},
                "description": "It's the end of the world as we know it.",
                "managers": [{"value": "admin", "info": ImportState.DONE, "id": 1}],
                "meeting_name": "Armageddon Countdown",
                "meeting_start_time": 1356048000,
                "meeting_end_time": 1356048000,
                "meeting_time_zone": {"info": ImportState.WARNING, "value": None},
                "meeting_admins": [
                    {"value": "admin", "info": ImportState.DONE, "id": 1}
                ],
            },
        }

    def json_upload_with_timezones(self) -> None:
        self.set_models({"organization/1": {"time_zone": "Europe/London"}})
        self.create_user("billieLondon")
        self.create_user("colinFrenchman")
        self.create_user("danSpain")
        self.create_user("evanPitkern")
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "Main Conference",
                        "description": "We discuss the important stuff here",
                        "managers": ["admin"],
                        "meeting_name": "Main Conference",
                        "meeting_start_time": "2027-01-01",
                        "meeting_end_time": "2027-01-02",
                        "meeting_admins": ["billieLondon"],
                    },
                    {
                        "name": "London Conference",
                        "managers": ["admin"],
                        "forward_to_committees": ["Main Conference"],
                        "meeting_name": "London Conference",
                        "meeting_start_time": "2026-12-01",
                        "meeting_end_time": "2026-12-02",
                        "meeting_time_zone": "Europe/London",
                        "meeting_admins": ["billieLondon"],
                    },
                    {
                        "name": "Guernsey Conference",
                        "managers": ["admin"],
                        "forward_to_committees": ["Main Conference"],
                        "meeting_name": "Guernsey Conference",
                        "meeting_start_time": "2026-12-01",
                        "meeting_end_time": "2026-12-02",
                        "meeting_time_zone": "Europe/Guernsey",
                        "meeting_admins": ["colinFrenchman"],
                    },
                    {
                        "name": "Gibraltar Conference",
                        "managers": ["admin"],
                        "forward_to_committees": ["Main Conference"],
                        "meeting_name": "Gibraltar Conference",
                        "meeting_start_time": "2026-12-01",
                        "meeting_end_time": "2026-12-02",
                        "meeting_time_zone": "Europe/Gibraltar",
                        "meeting_admins": ["danSpain"],
                    },
                    {
                        "name": "Pitcairn Conference",
                        "managers": ["admin"],
                        "forward_to_committees": ["Main Conference"],
                        "meeting_name": "Pitcairn Conference",
                        "meeting_start_time": "2026-12-01",
                        "meeting_end_time": "2026-12-02",
                        "meeting_time_zone": "Pacific/Pitcairn",
                        "meeting_admins": ["evanPitkern"],
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.WARNING
        assert len(response.json["results"][0][0]["rows"]) == 5
        assert self.get_row(response) == {
            "state": ImportState.NEW,
            "messages": [
                "Since no timezone was given, the dates will be interpreted as being in the 'Europe/London' zone."
            ],
            "data": {
                "name": {"info": ImportState.NEW, "value": "Main Conference"},
                "description": "We discuss the important stuff here",
                "managers": [{"value": "admin", "info": ImportState.DONE, "id": 1}],
                "meeting_name": "Main Conference",
                "meeting_start_time": 1798761600,
                "meeting_end_time": 1798848000,
                "meeting_time_zone": {"info": ImportState.WARNING, "value": None},
                "meeting_admins": [
                    {"value": "billieLondon", "info": ImportState.DONE, "id": 2}
                ],
            },
        }
        assert self.get_row(response, 1) == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": {"info": ImportState.NEW, "value": "London Conference"},
                "managers": [{"value": "admin", "info": ImportState.DONE, "id": 1}],
                "forward_to_committees": [
                    {"value": "Main Conference", "info": ImportState.DONE}
                ],
                "meeting_name": "London Conference",
                "meeting_start_time": 1796083200,
                "meeting_end_time": 1796169600,
                "meeting_time_zone": {
                    "info": ImportState.DONE,
                    "value": "Europe/London",
                },
                "meeting_admins": [
                    {"value": "billieLondon", "info": ImportState.DONE, "id": 2}
                ],
            },
        }
        assert self.get_row(response, 2) == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": {"info": ImportState.NEW, "value": "Guernsey Conference"},
                "managers": [{"value": "admin", "info": ImportState.DONE, "id": 1}],
                "forward_to_committees": [
                    {"value": "Main Conference", "info": ImportState.DONE}
                ],
                "meeting_name": "Guernsey Conference",
                "meeting_start_time": 1796083200,
                "meeting_end_time": 1796169600,
                "meeting_time_zone": {
                    "info": ImportState.DONE,
                    "value": "Europe/Guernsey",
                },
                "meeting_admins": [
                    {"value": "colinFrenchman", "info": ImportState.DONE, "id": 3}
                ],
            },
        }
        assert self.get_row(response, 3) == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": {"info": ImportState.NEW, "value": "Gibraltar Conference"},
                "managers": [{"value": "admin", "info": ImportState.DONE, "id": 1}],
                "forward_to_committees": [
                    {"value": "Main Conference", "info": ImportState.DONE}
                ],
                "meeting_name": "Gibraltar Conference",
                "meeting_start_time": 1796083200 - 3600,
                "meeting_end_time": 1796169600 - 3600,
                "meeting_time_zone": {
                    "info": ImportState.DONE,
                    "value": "Europe/Gibraltar",
                },
                "meeting_admins": [
                    {"value": "danSpain", "info": ImportState.DONE, "id": 4}
                ],
            },
        }
        assert self.get_row(response, 4) == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": {"info": ImportState.NEW, "value": "Pitcairn Conference"},
                "managers": [{"value": "admin", "info": ImportState.DONE, "id": 1}],
                "forward_to_committees": [
                    {"value": "Main Conference", "info": ImportState.DONE}
                ],
                "meeting_name": "Pitcairn Conference",
                "meeting_start_time": 1796083200 + 8 * 3600,
                "meeting_end_time": 1796169600 + 8 * 3600,
                "meeting_time_zone": {
                    "info": ImportState.DONE,
                    "value": "Pacific/Pitcairn",
                },
                "meeting_admins": [
                    {"value": "evanPitkern", "info": ImportState.DONE, "id": 5}
                ],
            },
        }

    def json_upload_meeting_template_not_found(self) -> None:
        self.create_user("bob")
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "test",
                        "meeting_name": "test meeting",
                        "meeting_template": "test",
                        "meeting_admins": ["bob"],
                        "meeting_time_zone": "Asia/Novosibirsk",
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
                "meeting_admins": [{"info": ImportState.DONE, "value": "bob", "id": 2}],
                "meeting_time_zone": {
                    "info": ImportState.DONE,
                    "value": "Asia/Novosibirsk",
                },
            },
        }
        self.assert_statistics(response, {"meetings_created": 1})

    def json_upload_admin_defined_meeting_template_found(self) -> None:
        """
        Also tests what happens if there's an orga timezone but no meeting times
        """
        self.set_models({"organization/1": {"time_zone": "Indian/Mauritius"}})
        self.create_meeting(2, meeting_data={"name": "template"})
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "Committee61",
                        "meeting_name": "test",
                        "meeting_template": "template",
                        "meeting_admins": [ADMIN_USERNAME],
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.DONE,
            "messages": [],
            "data": {
                "id": 61,
                "name": {"value": "Committee61", "info": ImportState.DONE, "id": 61},
                "meeting_name": "test",
                "meeting_template": {
                    "value": "template",
                    "info": ImportState.DONE,
                    "id": 2,
                },
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
            },
        }
        self.assert_statistics(response, {"meetings_created": 0, "meetings_cloned": 1})

    def json_upload_meeting_template_with_admins_found(self) -> None:
        self.create_meeting(2, meeting_data={"name": "template"})
        self.create_user("bob", [3])  # create admin for meeting 2
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "Committee61",
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
                "id": 61,
                "name": {"value": "Committee61", "info": ImportState.DONE, "id": 61},
                "meeting_name": "test",
                "meeting_template": {
                    "value": "template",
                    "info": ImportState.DONE,
                    "id": 2,
                },
            },
        }
        self.assert_statistics(response, {"meetings_created": 0, "meetings_cloned": 1})

    def json_upload_with_duplicated_organization_tags(
        self,
    ) -> None:
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {"name": "n1", "organization_tags": ["ot1", "ot2"]},
                    {"name": "n2", "organization_tags": ["ot1"]},
                ]
            },
        )
        self.assert_status_code(response, 200)
        self.assert_statistics(response, {"organization_tags_created": 2})
        assert self.get_row(response, 0) == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": {"value": "n1", "info": ImportState.NEW},
                "organization_tags": [
                    {"value": "ot1", "info": ImportState.NEW},
                    {"value": "ot2", "info": ImportState.NEW},
                ],
            },
        }
        assert self.get_row(response, 1) == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "name": {"value": "n2", "info": ImportState.NEW},
                "organization_tags": [
                    {"value": "ot1", "info": ImportState.DONE},
                ],
            },
        }

    def json_upload_with_parent(self) -> None:
        self.create_committee(name="one")
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "two",
                        "parent": "one",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.DONE
        assert self.get_row(response) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "two",
                },
                "parent": {"info": ImportState.DONE, "value": "one", "id": 1},
            },
            "messages": [],
            "state": ImportState.NEW,
        }

    def json_upload_with_parents(self) -> None:
        self.create_committee(name="one")
        self.create_committee(2, name="two")
        self.create_committee(3, name="three")
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {"name": "one"},
                    {
                        "name": "two",
                        "parent": "five",
                    },
                    {
                        "name": "three",
                        "parent": "two",
                    },
                    {
                        "name": "nine",
                        "parent": "eight",
                    },
                    {
                        "name": "four",
                    },
                    {"name": "five", "parent": "fourhundredandtwenty"},
                    {
                        "name": "six",
                        "parent": "five",
                    },
                    {
                        "name": "seven",
                        "parent": "five",
                    },
                    {
                        "name": "eight",
                        "parent": "seven",
                    },
                    {
                        "name": "ten",
                        "parent": "two",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.WARNING
        self.assert_parents_test_result(response)

    def assert_parents_test_result(self, response: Response) -> None:
        assert self.get_row(response) == {
            "data": {
                "id": 1,
                "name": {
                    "id": 1,
                    "info": ImportState.DONE,
                    "value": "one",
                },
            },
            "messages": [],
            "state": ImportState.DONE,
        }
        assert self.get_row(response, 1) == {
            "data": {
                "id": 2,
                "name": {
                    "id": 2,
                    "info": ImportState.DONE,
                    "value": "two",
                },
                "parent": {
                    "info": ImportState.NEW,
                    "value": "five",
                },
            },
            "messages": [],
            "state": ImportState.DONE,
        }
        assert self.get_row(response, 2) == {
            "data": {
                "id": 3,
                "name": {
                    "id": 3,
                    "info": ImportState.DONE,
                    "value": "three",
                },
                "parent": {
                    "id": 2,
                    "info": ImportState.DONE,
                    "value": "two",
                },
            },
            "messages": [],
            "state": ImportState.DONE,
        }
        assert self.get_row(response, 3) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "nine",
                },
                "parent": {
                    "info": ImportState.NEW,
                    "value": "eight",
                },
            },
            "messages": [],
            "state": ImportState.NEW,
        }
        assert self.get_row(response, 4) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "four",
                },
            },
            "messages": [],
            "state": ImportState.NEW,
        }
        assert self.get_row(response, 5) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "five",
                },
                "parent": {
                    "info": ImportState.WARNING,
                    "value": "",
                },
            },
            "messages": [
                "Could not identify parent: Name 'fourhundredandtwenty' not found, the field will therefore be ignored."
            ],
            "state": ImportState.NEW,
        }
        assert self.get_row(response, 6) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "six",
                },
                "parent": {
                    "info": ImportState.NEW,
                    "value": "five",
                },
            },
            "messages": [],
            "state": ImportState.NEW,
        }
        assert self.get_row(response, 7) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "seven",
                },
                "parent": {
                    "info": ImportState.NEW,
                    "value": "five",
                },
            },
            "messages": [],
            "state": ImportState.NEW,
        }
        assert self.get_row(response, 8) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "eight",
                },
                "parent": {
                    "info": ImportState.NEW,
                    "value": "seven",
                },
            },
            "messages": [],
            "state": ImportState.NEW,
        }
        assert self.get_row(response, 9) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "ten",
                },
                "parent": {
                    "id": 2,
                    "info": ImportState.DONE,
                    "value": "two",
                },
            },
            "messages": [],
            "state": ImportState.NEW,
        }

    def json_upload_update_parent_ids(self) -> None:
        self.create_committee(name="'mittee 1")
        self.create_committee(2, parent_id=1, name="'mittee 2")
        self.create_committee(3, parent_id=2, name="'mittee 3")
        self.create_committee(4, parent_id=3, name="'mittee 4")
        self.create_committee(5, parent_id=3, name="'mittee 5")
        self.create_committee(6, parent_id=2, name="'mittee 6")
        self.create_committee(7, parent_id=6, name="'mittee 7")
        self.create_committee(8, parent_id=6, name="'mittee 8")
        self.create_committee(9, parent_id=1, name="'mittee 9")
        self.create_committee(10, parent_id=9, name="'mittee a")
        self.create_committee(11, parent_id=10, name="'mittee b")
        self.create_committee(12, parent_id=10, name="'mittee c")
        self.create_committee(13, parent_id=9, name="'mittee d")
        self.create_committee(14, parent_id=13, name="'mittee e")
        self.create_committee(15, parent_id=13, name="'mittee f")
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {"name": "'mittee 3", "parent": "'mittee e"},
                    {"name": "'mittee a", "parent": "'mittee 4"},
                    {"name": "'mittee 5", "parent": "'mittee 6"},
                    {
                        "name": "'mittee 9",
                        "description": "Now this ain't just any ol' 'mittee, this is THE 'mittee I tell ya.",
                    },
                    {
                        "name": "'mittee b",
                        "parent": "'nother 'mittee",
                        "description": "Now we here ain't snobs like them guys from 'mittee 9, y'all can relax here.",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.WARNING
        assert self.get_row(response) == {
            "data": {
                "id": 3,
                "name": {
                    "id": 3,
                    "info": ImportState.DONE,
                    "value": "'mittee 3",
                },
                "parent": {
                    "id": 14,
                    "info": ImportState.DONE,
                    "value": "'mittee e",
                },
            },
            "messages": [],
            "state": ImportState.DONE,
        }
        assert self.get_row(response, 1) == {
            "data": {
                "id": 10,
                "name": {
                    "id": 10,
                    "info": ImportState.DONE,
                    "value": "'mittee a",
                },
                "parent": {
                    "id": 4,
                    "info": ImportState.DONE,
                    "value": "'mittee 4",
                },
            },
            "messages": [],
            "state": ImportState.DONE,
        }
        assert self.get_row(response, 2) == {
            "data": {
                "id": 5,
                "name": {
                    "id": 5,
                    "info": ImportState.DONE,
                    "value": "'mittee 5",
                },
                "parent": {
                    "id": 6,
                    "info": ImportState.DONE,
                    "value": "'mittee 6",
                },
            },
            "messages": [],
            "state": ImportState.DONE,
        }
        assert self.get_row(response, 3) == {
            "data": {
                "id": 9,
                "name": {"id": 9, "info": ImportState.DONE, "value": "'mittee 9"},
                "description": "Now this ain't just any ol' 'mittee, this is THE 'mittee I tell ya.",
            },
            "messages": [],
            "state": ImportState.DONE,
        }
        assert self.get_row(response, 4) == {
            "data": {
                "id": 11,
                "name": {"id": 11, "info": ImportState.DONE, "value": "'mittee b"},
                "parent": {"value": "", "info": ImportState.WARNING},
                "description": "Now we here ain't snobs like them guys from 'mittee 9, y'all can relax here.",
            },
            "messages": [
                "Could not identify parent: Name ''nother 'mittee' not found, the field will therefore be ignored."
            ],
            "state": ImportState.DONE,
        }

    def json_upload_parent_not_found(self) -> None:
        self.create_committee(name="National council")
        self.create_committee(2, name="Regional council")
        self.create_committee(3, parent_id=2, name="County council")
        self.create_committee(4, parent_id=3, name="District council")
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "National conference",
                        "parent": "National",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.WARNING
        assert self.get_row(response) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "National conference",
                },
                "parent": {
                    "info": ImportState.WARNING,
                    "value": "",
                },
            },
            "messages": [
                "Could not identify parent: Name 'National' not found, the field will therefore be ignored.",
            ],
            "state": ImportState.NEW,
        }

    def json_upload_parent_multiple_found(self) -> None:
        self.create_committee(name="National council")
        self.create_committee(2, name="Regional council")
        self.create_committee(3, parent_id=2, name="County council")
        self.create_committee(4, parent_id=3, name="District council")
        self.create_committee(5, name="National council")
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "Regional council",
                        "parent": "National council",
                    },
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.WARNING
        assert self.get_row(response) == {
            "data": {
                "id": 2,
                "name": {
                    "id": 2,
                    "info": ImportState.DONE,
                    "value": "Regional council",
                },
                "parent": {
                    "info": ImportState.WARNING,
                    "value": "",
                },
            },
            "messages": [
                "Could not identify parent: Name 'National council' found multiple times, the field will therefore be ignored.",
            ],
            "state": ImportState.DONE,
        }
