from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from psycopg.types.json import Jsonb

from openslides_backend.action.mixins.import_mixins import ImportState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.base import ADMIN_USERNAME
from tests.util import Response

from .test_json_upload import TestCommitteeJsonUploadForImport


class TestCommitteeImport(TestCommitteeJsonUploadForImport):
    def get_row(self, response: Response, index: int = 0) -> dict[str, Any]:
        return response.json["results"][0][0]["rows"][index]

    def test_import_correct(self) -> None:
        response = self.request(
            "committee.json_upload",
            {"data": [{"name": "test"}]},
        )
        self.assert_status_code(response, 200)
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists("committee/1", {"name": "test"})
        self.assert_model_not_exists("action_worker/1")

    def test_import_all_fields(self) -> None:
        self.json_upload_all_fields()
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("action_worker/1")
        self.assert_model_exists(
            "committee/2",
            {
                "name": "test",
                "description": "desc",
                "forward_to_committee_ids": [1],
                "organization_tag_ids": [1],
                "manager_ids": [1],
                "meeting_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting/1",
            {
                "committee_id": 2,
                "name": "meeting",
                "start_time": datetime.fromtimestamp(1691539200, ZoneInfo("UTC")),
                "end_time": datetime.fromtimestamp(1691625600, ZoneInfo("UTC")),
            },
        )
        self.assert_model_exists(
            "group/2",
            {
                "meeting_id": 1,
                "name": "Admin",
                "meeting_user_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "meeting_id": 1,
                "user_id": 2,
                "group_ids": [2],
            },
        )

    def test_import_cancel(self) -> None:
        response = self.request(
            "committee.json_upload",
            {"data": [{"name": "test"}]},
        )
        self.assert_status_code(response, 200)
        response = self.request("committee.import", {"id": 1, "import": False})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("committee/1")
        self.assert_model_not_exists("action_worker/1")

    def test_import_new_duplicate(self) -> None:
        response = self.request(
            "committee.json_upload",
            {"data": [{"name": "test"}]},
        )
        self.set_models({"committee/12": {"name": "test"}})

        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = self.get_row(response)
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            f"Error: row state expected to be '{ImportState.DONE}', but it is '{ImportState.NEW}'."
        ]

    def test_import_update_correct(self) -> None:
        self.set_models({"committee/12": {"name": "test"}})
        response = self.request(
            "committee.json_upload",
            {"data": [{"name": "test", "description": "test"}]},
        )
        self.assert_status_code(response, 200)
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/12", {"name": "test", "description": "test"}
        )

    def test_import_update_no_duplicate(self) -> None:
        self.set_models(
            {
                "import_preview/1": {
                    "name": "committee",
                    "state": ImportState.DONE,
                    "created": datetime.now(),
                    "result": Jsonb(
                        {
                            "rows": [
                                {
                                    "state": ImportState.DONE,
                                    "messages": [],
                                    "data": {
                                        "id": 12,
                                        "name": {
                                            "value": "test1",
                                            "state": ImportState.DONE,
                                            "id": 12,
                                        },
                                    },
                                },
                            ],
                        },
                    ),
                },
            }
        )
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = self.get_row(response)
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Error: committee 12 not found anymore for updating committee 'test1'."
        ]

    def test_import_update_id_mismatch(self) -> None:
        self.set_models(
            {
                "committee/15": {"name": "test1"},
                "import_preview/1": {
                    "name": "committee",
                    "state": ImportState.DONE,
                    "created": datetime.now(),
                    "result": Jsonb(
                        {
                            "rows": [
                                {
                                    "state": ImportState.DONE,
                                    "messages": [],
                                    "data": {
                                        "id": 12,
                                        "name": {
                                            "value": "test1",
                                            "state": ImportState.DONE,
                                            "id": 12,
                                        },
                                    },
                                },
                            ],
                        }
                    ),
                },
            }
        )

        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = self.get_row(response)
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Error: name 'test1' found in different id (15 instead of 12)"
        ]

    def test_import_update_name_mismatch(self) -> None:
        self.set_models({"committee/12": {"name": "test"}})
        response = self.request(
            "committee.json_upload",
            {"data": [{"name": "test"}]},
        )
        self.set_models({"committee/12": {"name": "other"}})

        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = self.get_row(response)
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Error: committee 12 not found anymore for updating committee 'test'."
        ]

    def test_import_update_missing_id(self) -> None:
        self.set_models(
            {
                "committee/12": {"name": "test"},
                "import_preview/1": {
                    "name": "committee",
                    "state": ImportState.DONE,
                    "created": datetime.now(),
                    "result": Jsonb(
                        {
                            "rows": [
                                {
                                    "state": ImportState.DONE,
                                    "messages": [],
                                    "data": {
                                        "name": {
                                            "value": "test",
                                            "state": ImportState.DONE,
                                            "id": 12,
                                        },
                                    },
                                },
                            ],
                        }
                    ),
                },
            }
        )
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 400)
        assert (
            f"Invalid JsonUpload data: A data row with state '{ImportState.DONE}' must have an 'id'"
            in response.json["message"]
        )

    def test_import_forwards(self) -> None:
        self.set_models(
            {
                "committee/12": {"name": "test"},
                "committee/13": {"name": "renamed_new"},
                "import_preview/1": {
                    "name": "committee",
                    "state": ImportState.DONE,
                    "created": datetime.now(),
                    "result": Jsonb(
                        {
                            "rows": [
                                {
                                    "state": ImportState.NEW,
                                    "messages": [],
                                    "data": {
                                        "name": {
                                            "value": "other",
                                            "info": ImportState.DONE,
                                        },
                                    },
                                },
                                {
                                    "state": ImportState.NEW,
                                    "messages": [],
                                    "data": {
                                        "name": {
                                            "value": "this",
                                            "info": ImportState.DONE,
                                        },
                                        "forward_to_committees": [
                                            {
                                                "value": "test",
                                                "info": ImportState.DONE,
                                                "id": 12,
                                            },
                                            {
                                                "value": "test2",
                                                "info": ImportState.WARNING,
                                            },
                                            {
                                                "value": "renamed_old",
                                                "info": ImportState.DONE,
                                                "id": 13,
                                            },
                                            {
                                                "value": "deleted",
                                                "info": ImportState.DONE,
                                                "id": 14,
                                            },
                                            {
                                                "value": "this",
                                                "info": ImportState.DONE,
                                            },
                                            {
                                                "value": "other",
                                                "info": ImportState.DONE,
                                            },
                                        ],
                                    },
                                },
                            ],
                        }
                    ),
                },
            }
        )
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = self.get_row(response, 1)
        assert row["messages"] == [
            "Expected model '13 renamed_old' changed its name to 'renamed_new'.",
            "Model '14 deleted' doesn't exist anymore",
        ]
        self.assert_model_exists(
            "committee/14",
            {"name": "other", "receive_forwardings_from_committee_ids": [15]},
        )
        self.assert_model_exists(
            "committee/15", {"name": "this", "forward_to_committee_ids": [12, 14, 15]}
        )

    def test_import_organization_tags(self) -> None:
        self.set_models(
            {
                "organization_tag/12": {"name": "test", "color": "#123456"},
                "organization_tag/13": {"name": "renamed_new", "color": "#FEDCBA"},
                "import_preview/1": {
                    "name": "committee",
                    "state": ImportState.DONE,
                    "created": datetime.now(),
                    "result": Jsonb(
                        {
                            "rows": [
                                {
                                    "state": ImportState.NEW,
                                    "messages": [],
                                    "data": {
                                        "name": {
                                            "value": "this",
                                            "info": ImportState.DONE,
                                        },
                                        "organization_tags": [
                                            {
                                                "value": "test",
                                                "info": ImportState.DONE,
                                                "id": 12,
                                            },
                                            {
                                                "value": "test2",
                                                "info": ImportState.WARNING,
                                            },
                                            {
                                                "value": "renamed_old",
                                                "info": ImportState.DONE,
                                                "id": 13,
                                            },
                                            {
                                                "value": "deleted",
                                                "info": ImportState.DONE,
                                                "id": 14,
                                            },
                                            {
                                                "value": "new",
                                                "info": ImportState.DONE,
                                            },
                                        ],
                                    },
                                },
                            ],
                        }
                    ),
                },
            }
        )
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = self.get_row(response)
        assert row["messages"] == [
            "Expected model '13 renamed_old' changed its name to 'renamed_new'.",
            "Model '14 deleted' doesn't exist anymore",
        ]
        self.assert_model_exists(
            "committee/1", {"name": "this", "organization_tag_ids": [12, 14]}
        )

    def test_import_with_duplicated_organization_tags(self) -> None:
        self.json_upload_with_duplicated_organization_tags()
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "organization_tag/1",
            {"name": "ot1", "tagged_ids": ["committee/1", "committee/2"]},
        )
        self.assert_model_exists(
            "organization_tag/2", {"name": "ot2", "tagged_ids": ["committee/1"]}
        )
        self.assert_model_not_exists("organization_tag/3")

    def test_import_managers(self) -> None:
        self.set_models(
            {
                "user/12": {"username": "test"},
                "user/13": {"username": "renamed_new"},
                "import_preview/1": {
                    "name": "committee",
                    "state": ImportState.DONE,
                    "created": datetime.now(),
                    "result": Jsonb(
                        {
                            "rows": [
                                {
                                    "state": ImportState.NEW,
                                    "messages": [],
                                    "data": {
                                        "name": {
                                            "value": "this",
                                            "info": ImportState.DONE,
                                        },
                                        "managers": [
                                            {
                                                "value": "test",
                                                "info": ImportState.DONE,
                                                "id": 12,
                                            },
                                            {
                                                "value": "test2",
                                                "info": ImportState.WARNING,
                                            },
                                            {
                                                "value": "renamed_old",
                                                "info": ImportState.DONE,
                                                "id": 13,
                                            },
                                            {
                                                "value": "deleted",
                                                "info": ImportState.DONE,
                                                "id": 14,
                                            },
                                        ],
                                    },
                                },
                            ],
                        }
                    ),
                },
            }
        )
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = self.get_row(response)
        assert row["messages"] == [
            "Expected model '13 renamed_old' changed its name to 'renamed_new'.",
            "Model '14 deleted' doesn't exist anymore",
        ]
        self.assert_model_exists("committee/1", {"name": "this", "manager_ids": [12]})

    def test_import_meeting_template(self) -> None:
        self.set_models(
            {
                "committee/12": {"name": "test1"},
                "committee/13": {"name": "test2"},
                "committee/14": {"name": "test3"},
                "committee/15": {"name": "test4"},
            }
        )
        self.create_meeting(
            meeting_data={
                "name": "test",
                "committee_id": 12,
                "description": "test",
            }
        )
        self.create_meeting(
            4,
            meeting_data={
                "name": "renamed_new",
                "committee_id": 14,
                "description": "test",
            },
        )
        self.set_models(
            {
                "import_preview/1": {
                    "name": "committee",
                    "state": ImportState.DONE,
                    "created": datetime.now(),
                    "result": Jsonb(
                        {
                            "rows": [
                                {
                                    "state": ImportState.DONE,
                                    "messages": [],
                                    "data": {
                                        "id": 12,
                                        "name": {
                                            "value": "test1",
                                            "info": ImportState.DONE,
                                        },
                                        "meeting_name": "meeting",
                                        "meeting_template": {
                                            "value": "test",
                                            "info": ImportState.DONE,
                                            "id": 1,
                                        },
                                        "meeting_admins": [
                                            {
                                                "info": ImportState.DONE,
                                                "value": ADMIN_USERNAME,
                                                "id": 1,
                                            }
                                        ],
                                    },
                                },
                                {
                                    "state": ImportState.DONE,
                                    "messages": [],
                                    "data": {
                                        "id": 13,
                                        "name": {
                                            "value": "test2",
                                            "info": ImportState.DONE,
                                        },
                                        "meeting_name": "meeting",
                                        "meeting_template": {
                                            "value": "missing",
                                            "info": ImportState.WARNING,
                                        },
                                        "meeting_admins": [
                                            {
                                                "info": ImportState.DONE,
                                                "value": ADMIN_USERNAME,
                                                "id": 1,
                                            }
                                        ],
                                    },
                                },
                                {
                                    "state": ImportState.DONE,
                                    "messages": [],
                                    "data": {
                                        "id": 14,
                                        "name": {
                                            "value": "test3",
                                            "info": ImportState.DONE,
                                        },
                                        "meeting_name": "meeting",
                                        "meeting_template": {
                                            "value": "renamed_old",
                                            "info": ImportState.DONE,
                                            "id": 4,
                                        },
                                        "meeting_admins": [
                                            {
                                                "info": ImportState.DONE,
                                                "value": ADMIN_USERNAME,
                                                "id": 1,
                                            }
                                        ],
                                    },
                                },
                                {
                                    "state": ImportState.DONE,
                                    "messages": [],
                                    "data": {
                                        "id": 15,
                                        "name": {
                                            "value": "test4",
                                            "info": ImportState.DONE,
                                        },
                                        "meeting_name": "meeting",
                                        "meeting_template": {
                                            "value": "deleted",
                                            "info": ImportState.DONE,
                                            "id": 17,
                                        },
                                        "meeting_admins": [
                                            {
                                                "info": ImportState.DONE,
                                                "value": ADMIN_USERNAME,
                                                "id": 1,
                                            }
                                        ],
                                    },
                                },
                            ],
                        }
                    ),
                },
            }
        )
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert self.get_row(response, 0) == {
            "data": {
                "id": 12,
                "name": {"info": "done", "value": "test1"},
                "meeting_name": "meeting",
                "meeting_template": {"id": 1, "info": "done", "value": "test"},
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
            },
            "messages": [],
            "state": "done",
        }
        self.assert_model_exists("committee/12", {"meeting_ids": [1, 8]})
        self.assert_model_exists(
            "meeting/8", {"name": "meeting", "committee_id": 12, "description": "test"}
        )
        assert self.get_row(response, 1) == {
            "data": {
                "id": 13,
                "name": {"info": "done", "value": "test2"},
                "meeting_name": "meeting",
                "meeting_template": {"info": "warning", "value": "missing"},
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
            },
            "messages": [],
            "state": "done",
        }
        self.assert_model_exists("committee/13", {"meeting_ids": [5]})
        self.assert_model_exists(
            "meeting/5",
            {
                "name": "meeting",
                "committee_id": 13,
                "description": "Presentation and assembly system",
            },
        )
        assert self.get_row(response, 2) == {
            "data": {
                "id": 14,
                "name": {"info": "done", "value": "test3"},
                "meeting_name": "meeting",
                "meeting_template": {
                    "id": 4,
                    "info": "warning",
                    "value": "renamed_old",
                },
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
            },
            "messages": [
                "Expected model '4 renamed_old' changed its name to 'renamed_new'."
            ],
            "state": "done",
        }
        self.assert_model_exists("committee/14", {"meeting_ids": [4, 6]})
        self.assert_model_exists(
            "meeting/6",
            {
                "name": "meeting",
                "committee_id": 14,
                "description": "Presentation and assembly system",
            },
        )
        assert self.get_row(response, 3) == {
            "data": {
                "id": 15,
                "name": {"info": "done", "value": "test4"},
                "meeting_name": "meeting",
                "meeting_template": {"id": 17, "info": "warning", "value": "deleted"},
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
            },
            "messages": ["Model '17 deleted' doesn't exist anymore"],
            "state": "done",
        }
        self.assert_model_exists("committee/15", {"meeting_ids": [7]})
        self.assert_model_exists(
            "meeting/7",
            {
                "name": "meeting",
                "committee_id": 15,
                "description": "Presentation and assembly system",
            },
        )

    def test_import_no_permission(self) -> None:
        response = self.request(
            "committee.json_upload",
            {"data": [{"name": "test"}]},
        )
        self.assert_status_code(response, 200)
        self.base_permission_test(
            {},
            "committee.import",
            {"id": 1, "import": True},
        )

    def test_import_permission(self) -> None:
        response = self.request(
            "committee.json_upload",
            {"data": [{"name": "test"}]},
        )
        self.assert_status_code(response, 200)
        self.base_permission_test(
            {},
            "committee.import",
            {"id": 1, "import": True},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )

    def test_json_upload_meeting_template_not_found(self) -> None:
        self.json_upload_meeting_template_not_found()
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert self.get_row(response, 0) == {
            "data": {
                "name": {"info": "new", "value": "test"},
                "meeting_name": "test meeting",
                "meeting_template": {"info": "warning", "value": "test"},
                "meeting_admins": [{"info": ImportState.DONE, "value": "bob", "id": 2}],
            },
            "messages": ["Template meetings can only be used for existing committees."],
            "state": "new",
        }
        self.assert_model_exists("committee/1", {"meeting_ids": [1]})
        self.assert_model_exists(
            "meeting/1", {"name": "test meeting", "committee_id": 1}
        )

    def test_json_upload_admin_defined_meeting_template_found(self) -> None:
        self.json_upload_admin_defined_meeting_template_found()
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert self.get_row(response, 0) == {
            "data": {
                "id": 61,
                "name": {"info": "done", "value": "Commitee61", "id": 61},
                "meeting_name": "test",
                "meeting_template": {"id": 2, "info": "done", "value": "template"},
                "meeting_admins": [
                    {"info": ImportState.DONE, "value": ADMIN_USERNAME, "id": 1}
                ],
            },
            "messages": [],
            "state": "done",
        }
        self.assert_model_exists("committee/61", {"meeting_ids": [2, 3]})
        self.assert_model_exists("meeting/3", {"name": "test", "committee_id": 61})

    def test_json_upload_meeting_template_with_admins_found(self) -> None:
        self.json_upload_meeting_template_with_admins_found()
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert self.get_row(response, 0) == {
            "data": {
                "id": 61,
                "name": {"info": "done", "value": "Commitee61", "id": 61},
                "meeting_name": "test",
                "meeting_template": {"id": 2, "info": "done", "value": "template"},
            },
            "messages": [],
            "state": "done",
        }
        self.assert_model_exists("committee/61", {"meeting_ids": [2, 3]})
        self.assert_model_exists("meeting/3", {"name": "test", "committee_id": 61})

    def test_json_upload_meeting_template_with_admins_no_longer_found(self) -> None:
        self.json_upload_meeting_template_with_admins_found()
        response = self.request("meeting.delete", {"id": 2})
        self.assert_status_code(response, 200)
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        preview_row = self.get_row(response, 0)
        assert preview_row["data"] == {
            "id": 61,
            "name": {"info": "done", "value": "Commitee61", "id": 61},
            "meeting_name": "test",
            "meeting_template": {"id": 2, "info": "warning", "value": "template"},
            "meeting_admins": [{"info": "error", "value": ""}],
        }
        assert sorted(preview_row["messages"]) == sorted(
            [
                "Error: Meeting cannot be created without admins",
                "Model '2 template' doesn't exist anymore",
            ]
        )
        assert preview_row["state"] == "error"
        self.assert_model_exists("committee/61", {"meeting_ids": None})
        self.assert_model_not_exists("meeting/3")

    def test_json_upload_meeting_template_admin_not_found_anymore(self) -> None:
        self.json_upload_meeting_template_not_found()
        self.request("user.delete", {"id": 2})
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        preview_row = self.get_row(response, 0)
        assert preview_row["data"] == {
            "name": {"info": "new", "value": "test"},
            "meeting_name": "test meeting",
            "meeting_template": {"info": "warning", "value": "test"},
            "meeting_admins": [
                {"info": ImportState.WARNING, "value": "bob", "id": 2},
                {"info": "error", "value": ""},
            ],
        }
        assert sorted(preview_row["messages"]) == sorted(
            [
                "Template meetings can only be used for existing committees.",
                "Model '2 bob' doesn't exist anymore",
                "Error: Meeting cannot be created without admins",
            ]
        )
        assert preview_row["state"] == "error"
        self.assert_model_not_exists("committee/1")
        self.assert_model_not_exists("meeting/1")

    def test_json_upload_with_parents(self) -> None:
        self.json_upload_with_parents()
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_parents_test_result(response)
        expected_structure: dict[
            int,
            tuple[
                str, int | None, list[int] | None, list[int] | None, list[int] | None
            ],
        ] = {
            1: ("one", None, None, None, None),
            2: ("two", 6, [3, 10], [6], [3, 10]),
            3: ("three", 2, None, [2, 6], None),
            4: ("nine", 9, None, [6, 8, 9], None),
            5: ("four", None, None, None, None),
            6: ("five", None, [2, 7, 8], None, [2, 3, 4, 7, 8, 9, 10]),
            7: ("six", 6, None, [6], None),
            8: ("seven", 6, [9], [6], [4, 9]),
            9: ("eight", 8, [4], [6, 8], [4]),
            10: ("ten", 2, None, [2, 6], None),
        }
        for id_, (
            name,
            parent,
            child_ids,
            all_parent_ids,
            all_child_ids,
        ) in expected_structure.items():
            self.assert_model_exists(
                f"committee/{id_}",
                {
                    "name": name,
                    "parent_id": parent,
                    "child_ids": child_ids,
                    "all_parent_ids": all_parent_ids,
                    "all_child_ids": all_child_ids,
                },
            )

    def test_json_upload_parent_changed_name(self) -> None:
        self.json_upload_with_parents()
        self.set_models({"committee/2": {"name": "Committee two"}})
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.ERROR
        assert self.get_row(response, 1) == {
            "data": {
                "id": 2,
                "name": {
                    "id": 2,
                    "info": ImportState.ERROR,
                    "value": "two",
                },
                "parent": {
                    "info": ImportState.NEW,
                    "value": "five",
                },
            },
            "messages": [
                "Error: committee 2 not found anymore for updating committee 'two'.",
            ],
            "state": ImportState.ERROR,
        }
        assert self.get_row(response, 9) == {
            "data": {
                "name": {
                    "info": ImportState.NEW,
                    "value": "ten",
                },
                "parent": {
                    "id": 2,
                    "info": ImportState.WARNING,
                    "value": "two",
                },
            },
            "messages": ["Expected model '2 two' changed its name to 'Committee two'."],
            "state": ImportState.NEW,
        }

    def test_json_upload_parent_changed_name_2(self) -> None:
        self.json_upload_with_parent()
        self.set_models({"committee/1": {"name": "Committee one"}})
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.DONE
        assert self.get_row(response) == {
            "data": {
                "name": {"info": ImportState.NEW, "value": "two"},
                "parent": {"info": ImportState.WARNING, "value": "one", "id": 1},
            },
            "messages": ["Expected model '1 one' changed its name to 'Committee one'."],
            "state": ImportState.NEW,
        }
        self.assert_model_exists("committee/2", {"name": "two", "parent_id": 1})

    def test_json_upload_committee_with_new_committee_name_created(self) -> None:
        self.json_upload_with_parents()
        self.create_committee(4, name="ten")
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert self.get_row(response, 9) == {
            "data": {
                "name": {
                    "info": ImportState.ERROR,
                    "value": "ten",
                },
                "parent": {
                    "id": 2,
                    "info": ImportState.DONE,
                    "value": "two",
                },
            },
            "messages": ["Error: row state expected to be 'done', but it is 'new'."],
            "state": ImportState.ERROR,
        }
        self.assert_model_not_exists("committee/5")

    def test_json_upload_parent_deleted(self) -> None:
        self.json_upload_with_parent()
        response = self.request("committee.delete", {"id": 1})
        self.assert_status_code(response, 200)
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 400)
        assert "Model 'committee/1' does not exist." in response.json["message"]

    def test_json_upload_update_parent_ids(self) -> None:
        self.json_upload_update_parent_ids()
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/1",
            {
                "parent_id": None,
                "all_parent_ids": None,
                "child_ids": [2, 9],
                "all_child_ids": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            },
        )
        self.assert_model_exists(
            "committee/2",
            {
                "parent_id": 1,
                "all_parent_ids": [1],
                "child_ids": [6],
                "all_child_ids": [5, 6, 7, 8],
            },
        )
        self.assert_model_exists(
            "committee/3",
            {
                "parent_id": 14,
                "all_parent_ids": [1, 9, 13, 14],
                "child_ids": [4],
                "all_child_ids": [4, 10, 11, 12],
            },
        )
        self.assert_model_exists(
            "committee/4",
            {
                "parent_id": 3,
                "all_parent_ids": [1, 3, 9, 13, 14],
                "child_ids": [10],
                "all_child_ids": [10, 11, 12],
            },
        )
        self.assert_model_exists(
            "committee/5",
            {
                "parent_id": 6,
                "all_parent_ids": [1, 2, 6],
                "child_ids": None,
                "all_child_ids": None,
            },
        )
        self.assert_model_exists(
            "committee/6",
            {
                "parent_id": 2,
                "all_parent_ids": [1, 2],
                "child_ids": [5, 7, 8],
                "all_child_ids": [5, 7, 8],
            },
        )
        for id_ in [7, 8]:
            self.assert_model_exists(
                f"committee/{id_}",
                {
                    "parent_id": 6,
                    "all_parent_ids": [1, 2, 6],
                    "child_ids": None,
                    "all_child_ids": None,
                },
            )
        self.assert_model_exists(
            "committee/9",
            {
                "parent_id": 1,
                "all_parent_ids": [1],
                "child_ids": [13],
                "all_child_ids": [3, 4, 10, 11, 12, 13, 14, 15],
                "description": "Now this ain't just any ol' 'mittee, this is THE 'mittee I tell ya.",
            },
        )
        self.assert_model_exists(
            "committee/10",
            {
                "parent_id": 4,
                "all_parent_ids": [1, 3, 4, 9, 13, 14],
                "child_ids": [11, 12],
                "all_child_ids": [11, 12],
            },
        )
        self.assert_model_exists(
            "committee/11",
            {
                "parent_id": 10,
                "all_parent_ids": [1, 3, 4, 9, 10, 13, 14],
                "child_ids": None,
                "all_child_ids": None,
                "description": "Now we here ain't snobs like them guys from 'mittee 9, y'all can relax here.",
            },
        )
        self.assert_model_exists(
            "committee/12",
            {
                "parent_id": 10,
                "all_parent_ids": [1, 3, 4, 9, 10, 13, 14],
                "child_ids": None,
                "all_child_ids": None,
            },
        )
        self.assert_model_exists(
            "committee/13",
            {
                "parent_id": 9,
                "all_parent_ids": [1, 9],
                "child_ids": [14, 15],
                "all_child_ids": [3, 4, 10, 11, 12, 14, 15],
            },
        )
        self.assert_model_exists(
            "committee/14",
            {
                "parent_id": 13,
                "all_parent_ids": [1, 9, 13],
                "child_ids": [3],
                "all_child_ids": [3, 4, 10, 11, 12],
            },
        )
        self.assert_model_exists(
            "committee/15",
            {
                "parent_id": 13,
                "all_parent_ids": [1, 9, 13],
                "child_ids": None,
                "all_child_ids": None,
            },
        )

    def test_json_upload_parent_not_found(self) -> None:
        self.json_upload_parent_not_found()
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/5",
            {
                "parent_id": None,
                "name": "National conference",
            },
        )

    def test_json_upload_parent_multiple_found(self) -> None:
        self.json_upload_parent_multiple_found()
        self.assert_model_exists(
            "committee/2",
            {
                "parent_id": None,
                "name": "Regional council",
                "child_ids": [3],
                "all_child_ids": [3, 4],
            },
        )
