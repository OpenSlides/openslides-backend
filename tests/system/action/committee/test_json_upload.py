from math import ceil, floor
from time import time
from typing import Any

from openslides_backend.action.mixins.import_mixins import ImportState, StatisticEntry
from openslides_backend.models.models import Meeting
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
            "messages": [],
            "data": {
                "name": {"value": "test", "info": ImportState.NEW},
                "meeting_name": "test meeting",
                "meeting_start_time": 1691539200,
                "meeting_end_time": 1691625600,
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
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
                        "meeting_admins": [ADMIN_USERNAME],
                    }
                ]
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_row(response) == {
            "state": ImportState.ERROR,
            "messages": ["Error: A meeting with this name and dates already exists."],
            "data": {
                "id": 1,
                "name": {"value": "committee", "info": ImportState.DONE, "id": 1},
                "meeting_name": "meeting",
                "meeting_start_time": 1691539200,
                "meeting_end_time": 1691625600,
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
                "Error: Only one of start_time and end_time is not allowed.",
            ],
            "data": {
                "name": {"value": "test", "info": ImportState.NEW},
                "meeting_name": "test meeting",
                "meeting_start_time": 1691539200,
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
            },
        }
        assert self.get_row(response, 1) == {
            "state": ImportState.ERROR,
            "messages": [
                "Error: Only one of start_time and end_time is not allowed.",
            ],
            "data": {
                "name": {"value": "test2", "info": ImportState.NEW},
                "meeting_name": "test meeting 2",
                "meeting_end_time": 1691625600,
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
                "Error: start_time must be before end_time.",
            ],
            "data": {
                "name": {"value": "test", "info": ImportState.NEW},
                "meeting_name": "test meeting",
                "meeting_start_time": 1691625600,
                "meeting_end_time": 1691539200,
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
            "state": ImportState.ERROR,
            "messages": ["Error: Meeting cannot be created without admins"],
            "data": {
                "id": 1,
                "name": {"value": "committee", "info": ImportState.DONE, "id": 1},
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
                "id": 2,
                "name": {"value": "committee2", "info": ImportState.DONE, "id": 2},
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

    def test_json_upload_parent_not_found(self) -> None:
        self.create_committees_for_parent_tests()
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
        assert response.json["results"][0][0]["state"] == ImportState.ERROR
        assert self.get_row(response) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "National conference",
                },
                "parent": {
                    "info": ImportState.ERROR,
                    "value": "National",
                },
            },
            "messages": [
                "Error: Parent committee not found.",
            ],
            "state": ImportState.ERROR,
        }

    def test_json_upload_parent_multiple_found(self) -> None:
        self.create_committees_for_parent_tests()
        self.create_committee(5, name="National council")
        response = self.request(
            "committee.json_upload",
            {
                "data": [
                    {
                        "name": "National conference",
                        "parent": "National council",
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
                    "value": "National conference",
                },
                "parent": {
                    "info": ImportState.ERROR,
                    "value": "National council",
                },
            },
            "messages": [
                "Error: Found multiple committees with the same name as the parent.",
            ],
            "state": ImportState.ERROR,
        }

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
                "meeting_admins": [
                    {"value": "meeting_admin", "info": ImportState.DONE, "id": 2}
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
            },
        }
        self.assert_statistics(response, {"meetings_created": 1})

    def json_upload_admin_defined_meeting_template_found(self) -> None:
        self.create_meeting(2)
        self.set_models(
            {
                "committee/61": {"name": "committee"},
                "meeting/2": {
                    "name": "template",
                    "language": "en",
                    "reference_projector_id": 1,
                    "projector_ids": [1],
                    "motion_workflow_ids": [2],
                    "motion_state_ids": [2],
                    "motions_default_amendment_workflow_id": 2,
                    **{field: [1] for field in Meeting.all_default_projectors()},
                },
                "projector/1": {
                    "sequential_number": 1,
                    "meeting_id": 2,
                    "used_as_reference_projector_meeting_id": 2,
                    "name": "Default projector",
                    **{field: 2 for field in Meeting.reverse_default_projectors()},
                },
                "motion_workflow/2": {
                    "name": "yay",
                    "default_amendment_workflow_meeting_id": 2,
                    "sequential_number": 1,
                },
                "motion_state/2": {"weight": 1, "name": "dismissed"},
                "user/2": {"organization_id": 1},
                "organization/1": {"user_ids": [1, 2]},
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
                "name": {"value": "committee", "info": ImportState.DONE, "id": 61},
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
        self.create_meeting(2)
        self.create_user("bob", [3])  # create admin for meeting 2
        self.set_models(
            {
                "committee/61": {"name": "committee"},
                "meeting/2": {
                    "name": "template",
                    "language": "en",
                    "reference_projector_id": 1,
                    "projector_ids": [1],
                    "motion_workflow_ids": [2],
                    "motion_state_ids": [2],
                    "motions_default_amendment_workflow_id": 2,
                    **{field: [1] for field in Meeting.all_default_projectors()},
                },
                "projector/1": {
                    "sequential_number": 1,
                    "meeting_id": 2,
                    "used_as_reference_projector_meeting_id": 2,
                    "name": "Default projector",
                    **{field: 2 for field in Meeting.reverse_default_projectors()},
                },
                "motion_workflow/2": {
                    "name": "yay",
                    "default_amendment_workflow_meeting_id": 2,
                    "sequential_number": 1,
                },
                "motion_state/2": {"weight": 1, "name": "dismissed"},
                "user/2": {"organization_id": 1},
                "organization/1": {"user_ids": [1, 2]},
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
                "id": 61,
                "name": {"value": "committee", "info": ImportState.DONE, "id": 61},
                "meeting_name": "test",
                "meeting_template": {
                    "value": "template",
                    "info": ImportState.DONE,
                    "id": 2,
                },
            },
        }
        self.assert_statistics(response, {"meetings_created": 0, "meetings_cloned": 1})

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
                    {
                        "name": "five",
                    },
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
                    "info": ImportState.WARNING,
                    "value": "",
                },
            },
            "messages": [
                "The parent field will be skipped, because parent can not be updated for an existing committee.",
            ],
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
                    "info": ImportState.WARNING,
                    "value": "",
                },
            },
            "messages": [
                "The parent field will be skipped, because parent can not be updated "
                "for an existing committee.",
            ],
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
            },
            "messages": [],
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
