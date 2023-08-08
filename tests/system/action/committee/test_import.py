import pytest

from openslides_backend.action.mixins.import_mixins import ImportState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class CommitteeImport(BaseActionTestCase):
    def test_import_correct(self) -> None:
        self.set_models(
            {
                "committee/12": {"name": "test2"},
                "action_worker/1": {
                    "result": {
                        "import": "committee",
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "name": {"value": "test1", "info": ImportState.NEW}
                                },
                            },
                            {
                                "state": ImportState.DONE,
                                "messages": [],
                                "data": {
                                    "name": {
                                        "value": "test2",
                                        "info": ImportState.DONE,
                                        "id": 12,
                                    },
                                    "description": "blablabla",
                                },
                            },
                        ],
                    },
                },
            }
        )

        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists("committee/13", {"name": "test1"})
        self.assert_model_exists(
            "committee/12", {"name": "test2", "description": "blablabla"}
        )
        self.assert_model_not_exists("action_worker/1")

    def test_import_new_duplicate(self) -> None:
        self.set_models(
            {
                "committee/12": {"name": "test1"},
                "action_worker/1": {
                    "result": {
                        "import": "committee",
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "name": {"value": "test1", "info": ImportState.NEW}
                                },
                            },
                        ],
                    },
                },
            }
        )

        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == ["Want to create new committee, but name exists."]

    def test_import_update_no_duplicate(self) -> None:
        self.set_models(
            {
                "action_worker/1": {
                    "result": {
                        "import": "committee",
                        "rows": [
                            {
                                "state": ImportState.DONE,
                                "messages": [],
                                "data": {
                                    "name": {
                                        "value": "test1",
                                        "info": ImportState.DONE,
                                        "id": 12,
                                    }
                                },
                            },
                        ],
                    },
                },
            }
        )
        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == ["Want to update committee, but could not find it."]

    def test_import_update_id_mismatches(self) -> None:
        self.set_models(
            {
                "committee/15": {"name": "test1"},
                "action_worker/1": {
                    "result": {
                        "import": "committee",
                        "rows": [
                            {
                                "state": ImportState.DONE,
                                "messages": [],
                                "data": {
                                    "name": {
                                        "value": "test1",
                                        "info": ImportState.DONE,
                                        "id": 12,
                                    }
                                },
                            },
                        ],
                    },
                },
            }
        )

        response = self.request("committee.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        entry = response.json["results"][0][0]["rows"][0]
        assert entry["state"] == ImportState.ERROR
        assert entry["messages"] == ["Want to update committee, but id mismatches."]

    @pytest.mark.skip
    def test_import_new_and_done(self) -> None:
        self.set_models(
            {
                "committee/12": {"name": "test1"},
                "organization_tag/7": {"name": "ot1"},
                "user/5": {"username": "u1"},
                "action_worker/1": {
                    "result": {
                        "import": "committee",
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "name": {
                                        "value": "new committee",
                                        "info": ImportState.NEW,
                                    },
                                    "forward_to_committees": [
                                        {
                                            "value": "test1",
                                            "info": ImportState.DONE,
                                            "id": 12,
                                        },
                                        {"value": "test2", "info": ImportState.NEW},
                                    ],
                                    "organization_tags": [
                                        {
                                            "value": "ot1",
                                            "info": ImportState.DONE,
                                            "id": 7,
                                        },
                                        {"value": "ot2", "info": ImportState.NEW},
                                    ],
                                    "committee_managers": [
                                        {
                                            "value": "u1",
                                            "info": ImportState.DONE,
                                            "id": 5,
                                        },
                                        {"value": "u2", "info": ImportState.WARNING},
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
        self.assert_model_exists(
            "organization_tag/7", {"name": "ot1", "tagged_ids": ["committee/14"]}
        )
        self.assert_model_exists(
            "organization_tag/8", {"name": "ot2", "tagged_ids": ["committee/14"]}
        )
        self.assert_model_exists(
            "user/5",
            {"username": "u1", "commttee_management_ids": [14]},
        )
        self.assert_model_exists(
            "committee/14",
            {
                "name": "new committee",
                "forward_to_committee_ids": [12, 13],
                "organization_tag_ids": [7, 8],
                "manager_ids": [5],
            },
        )
        self.assert_model_exists(
            "committee/12",
            {"name": "test1", "receive_forwardings_from_committee_ids": [14]},
        )
        self.assert_model_exists(
            "committee/13",
            {"name": "test2", "receive_forwardings_from_committee_ids": [14]},
        )

    @pytest.mark.skip
    def test_import_reuse_fresh_created(self) -> None:
        self.set_models(
            {
                "action_worker/1": {
                    "result": {
                        "import": "committee",
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "name": {
                                        "value": "new committee",
                                        "info": ImportState.NEW,
                                    },
                                    "forward_to_committees": [
                                        {"value": "test1", "info": ImportState.NEW}
                                    ],
                                    "organization_tags": [
                                        {"value": "ot", "info": ImportState.NEW}
                                    ],
                                },
                            },
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "name": {
                                        "value": "new committee 2",
                                        "info": ImportState.NEW,
                                    },
                                    "forward_to_committees": [
                                        {"value": "test1", "info": ImportState.DONE}
                                    ],
                                    "organization_tags": [
                                        {"value": "ot", "info": ImportState.DONE}
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
        self.assert_model_exists(
            "committee/1",
            {"name": "test1", "receive_forwardings_from_committee_ids": [2, 3]},
        )
        self.assert_model_exists(
            "organization_tag/1",
            {"name": "ot", "tagged_ids": ["committee/2", "committee/3"]},
        )
        self.assert_model_not_exists("organization_tag/2")
        self.assert_model_exists(
            "committee/2",
            {
                "name": "new committee",
                "forward_to_committee_ids": [1],
                "organization_tag_ids": [1],
            },
        )
        self.assert_model_exists(
            "committee/3",
            {
                "name": "new committee 2",
                "forward_to_committee_ids": [1],
                "organization_tag_ids": [1],
            },
        )

    def test_import_create_meeting(self) -> None:
        self.set_models(
            {
                "organization/1": {
                    "default_language": "de",
                    "limit_of_meetings": 0,
                    "active_meeting_ids": [],
                },
                "user/5": {"username": "u1"},
                "action_worker/1": {
                    "result": {
                        "import": "committee",
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "name": {"value": "test1", "info": ImportState.NEW},
                                    "meeting_name": "meeting 1",
                                    "start_time": 1684844525,
                                    "end_time": 1684844546,
                                    "meeting_admins": [
                                        {
                                            "value": "u1",
                                            "info": ImportState.DONE,
                                            "id": 5,
                                        },
                                        {"value": "u2", "info": ImportState.WARNING},
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
        self.assert_model_exists(
            "meeting/1",
            {
                "name": "meeting 1",
                "start_time": 1684844525,
                "end_time": 1684844546,
                "committee_id": 1,
                "language": "de",
            },
        )
        self.assert_model_exists("user/5", {"username": "u1", "meeting_ids": [1]})
        self.assert_model_exists(
            "meeting_user/1", {"user_id": 5, "meeting_id": 1, "group_ids": [2]}
        )
        self.assert_model_exists("committee/1", {"name": "test1", "meeting_ids": [1]})

    def test_import_organization_tags(self) -> None:
        self.set_models(
            {
                "organization_tag/37": {"name": "test"},
                "action_worker/1": {
                    "result": {
                        "import": "committee",
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "name": {"value": "test1", "info": ImportState.NEW},
                                    "organization_tags": [
                                        {
                                            "value": "test",
                                            "info": ImportState.NEW,
                                            "id": 37,
                                        },
                                        {"value": "new", "info": ImportState.NEW},
                                        {"value": "test", "info": ImportState.WARNING},
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
        self.assert_model_exists(
            "committee/1", {"name": "test1", "organization_tag_ids": [37, 38]}
        )
        self.assert_model_exists(
            "organization_tag/37", {"name": "test", "tagged_ids": ["committee/1"]}
        )
        self.assert_model_exists(
            "organization_tag/38", {"name": "new", "tagged_ids": ["committee/1"]}
        )

    def test_import_managers(self) -> None:
        self.set_models(
            {
                "user/5": {"username": "test"},
                "action_worker/1": {
                    "result": {
                        "import": "committee",
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "name": {"value": "test1", "info": ImportState.NEW},
                                    "committee_managers": [
                                        {
                                            "value": "test",
                                            "info": ImportState.NEW,
                                            "id": 5,
                                        },
                                        {
                                            "value": "unknown",
                                            "info": ImportState.WARNING,
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
        self.assert_model_exists("committee/1", {"name": "test1", "manager_ids": [5]})
        self.assert_model_exists(
            "user/5", {"username": "test", "committee_management_ids": [1]}
        )

    def test_import_forward_to_committees(self) -> None:
        self.set_models(
            {
                "committee/5": {"name": "test"},
                "action_worker/1": {
                    "result": {
                        "import": "committee",
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "name": {"value": "test1", "info": ImportState.NEW},
                                    "forward_to_committees": [
                                        {
                                            "value": "test",
                                            "info": ImportState.NEW,
                                            "id": 5,
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
        self.assert_model_exists(
            "committee/6", {"name": "test1", "forward_to_committee_ids": [5]}
        )
        self.assert_model_exists(
            "committee/5",
            {"name": "test", "receive_forwardings_from_committee_ids": [6]},
        )

    def test_import_no_permission(self) -> None:
        self.base_permission_test(
            {
                "action_worker/2": {
                    "result": {
                        "import": "committee",
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "name": {"value": "test1", "info": ImportState.NEW}
                                },
                            },
                        ],
                    }
                }
            },
            "committee.import",
            {"id": 2, "import": True},
        )

    def test_import_permission(self) -> None:
        self.base_permission_test(
            {
                "action_worker/2": {
                    "result": {
                        "import": "committee",
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "name": {"value": "test1", "info": ImportState.NEW}
                                },
                            },
                        ],
                    }
                }
            },
            "committee.import",
            {"id": 2, "import": True},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
