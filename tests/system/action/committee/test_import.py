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
                                "data": {"name": "test1"},
                            },
                            {
                                "state": ImportState.DONE,
                                "messages": [],
                                "data": {
                                    "name": "test2",
                                    "description": "blablabla",
                                    "id": 12,
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
                                "data": {"name": "test1"},
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
                                "data": {"name": "test1", "id": 12},
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
                                "data": {"name": "test1", "id": 12},
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
                                "data": {"name": "test1"},
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
                                "data": {"name": "test1"},
                            },
                        ],
                    }
                }
            },
            "committee.import",
            {"id": 2, "import": True},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
