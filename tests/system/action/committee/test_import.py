from typing import Any, Dict

from openslides_backend.action.mixins.import_mixins import ImportState
from openslides_backend.models.models import Meeting
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.util import Response

from .test_json_upload import TestCommitteeJsonUploadForImport


class TestCommitteeImport(TestCommitteeJsonUploadForImport):
    def get_row(self, response: Response, index: int = 0) -> Dict[str, Any]:
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
                "start_time": 1691539200,
                "end_time": 1691625600,
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
        self.set_models(
            {
                "committee/12": {"name": "test"},
            }
        )

        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        row = self.get_row(response)
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            f"Error: row state expected to be '{ImportState.DONE}', but it is '{ImportState.NEW}'."
        ]

    def test_import_update_correct(self) -> None:
        self.set_models(
            {
                "committee/12": {"name": "test"},
            }
        )
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
                    "result": {
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
                    "result": {
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
        self.set_models(
            {
                "committee/12": {"name": "test"},
            }
        )
        response = self.request(
            "committee.json_upload",
            {"data": [{"name": "test"}]},
        )
        self.set_models(
            {
                "committee/12": {"name": "other"},
            }
        )

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
                    "result": {
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
                    },
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
                    "result": {
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
                                        {"value": "test2", "info": ImportState.WARNING},
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
                    },
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
            "committee/15", {"name": "this", "forward_to_committee_ids": [12, 15, 14]}
        )

    def test_import_organization_tags(self) -> None:
        self.set_models(
            {
                "organization_tag/12": {"name": "test"},
                "organization_tag/13": {"name": "renamed_new"},
                "import_preview/1": {
                    "name": "committee",
                    "state": ImportState.DONE,
                    "result": {
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
                                        {"value": "test2", "info": ImportState.WARNING},
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
                    },
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

    def test_import_managers(self) -> None:
        self.set_models(
            {
                "user/12": {"username": "test"},
                "user/13": {"username": "renamed_new"},
                "import_preview/1": {
                    "name": "committee",
                    "state": ImportState.DONE,
                    "result": {
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
                                        {"value": "test2", "info": ImportState.WARNING},
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
                    },
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
                "committee/12": {"name": "test1", "meeting_ids": [1]},
                "committee/13": {"name": "test2"},
                "committee/14": {"name": "test3", "meeting_ids": [2]},
                "committee/15": {"name": "test4"},
                "meeting/1": {
                    "name": "test",
                    "committee_id": 12,
                    "description": "test",
                    "language": "en",
                    "default_group_id": 1,
                    "motions_default_amendment_workflow_id": 1,
                    "motions_default_statute_amendment_workflow_id": 1,
                    "motions_default_workflow_id": 1,
                    "reference_projector_id": 1,
                    "projector_ids": [1],
                    "group_ids": [1],
                    "motion_state_ids": [1],
                    "motion_workflow_ids": [1],
                    **{field: [1] for field in Meeting.all_default_projectors()},
                    "is_active_in_organization_id": 1,
                },
                "group/1": {
                    "meeting_id": 1,
                    "name": "default group",
                    "weight": 1,
                    "default_group_for_meeting_id": 1,
                },
                "motion_workflow/1": {
                    "meeting_id": 1,
                    "name": "blup",
                    "first_state_id": 1,
                    "default_amendment_workflow_meeting_id": 1,
                    "default_statute_amendment_workflow_meeting_id": 1,
                    "default_workflow_meeting_id": 1,
                    "state_ids": [1],
                    "sequential_number": 1,
                },
                "motion_state/1": {
                    "css_class": "lightblue",
                    "meeting_id": 1,
                    "workflow_id": 1,
                    "name": "test",
                    "weight": 1,
                    "workflow_id": 1,
                    "first_state_of_workflow_id": 1,
                },
                "projector/1": {
                    "sequential_number": 1,
                    "meeting_id": 1,
                    "used_as_reference_projector_meeting_id": 1,
                    "name": "Default projector",
                    **{field: 1 for field in Meeting.reverse_default_projectors()},
                },
                "meeting/2": {
                    "name": "renamed_new",
                    "committee_id": 14,
                    "description": "test",
                },
                "import_preview/1": {
                    "name": "committee",
                    "state": ImportState.DONE,
                    "result": {
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
                                        "id": 2,
                                    },
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
                                },
                            },
                        ],
                    },
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
            },
            "messages": [],
            "state": "done",
        }
        self.assert_model_exists("committee/12", {"meeting_ids": [1, 6]})
        self.assert_model_exists(
            "meeting/6", {"name": "meeting", "committee_id": 12, "description": "test"}
        )
        assert self.get_row(response, 1) == {
            "data": {
                "id": 13,
                "name": {"info": "done", "value": "test2"},
                "meeting_name": "meeting",
                "meeting_template": {"info": "warning", "value": "missing"},
            },
            "messages": [],
            "state": "done",
        }
        self.assert_model_exists("committee/13", {"meeting_ids": [3]})
        self.assert_model_exists(
            "meeting/3",
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
                    "id": 2,
                    "info": "warning",
                    "value": "renamed_old",
                },
            },
            "messages": [
                "Expected model '2 renamed_old' changed its name to 'renamed_new'."
            ],
            "state": "done",
        }
        self.assert_model_exists("committee/14", {"meeting_ids": [2, 4]})
        self.assert_model_exists(
            "meeting/4",
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
            },
            "messages": ["Model '17 deleted' doesn't exist anymore"],
            "state": "done",
        }
        self.assert_model_exists("committee/15", {"meeting_ids": [5]})
        self.assert_model_exists(
            "meeting/5",
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
