from openslides_backend.action.mixins.import_mixins import ImportState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class UserJsonImport(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "action_worker/2": {
                    "result": {
                        "import": "account",
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "error": [],
                                "data": {
                                    "username": {
                                        "value": "test",
                                        "info": ImportState.DONE,
                                    },
                                    "first_name": "Testy",
                                },
                            },
                        ],
                    },
                },
                "action_worker/3": {
                    "result": {
                        "import": "account",
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "error": [],
                                "data": {
                                    "username": {
                                        "value": "TestyTester",
                                        "info": ImportState.DONE,
                                    },
                                    "first_name": "Testy",
                                    "last_name": "Tester",
                                    "email": "email@test.com",
                                    "gender": "male",
                                },
                            },
                        ],
                    },
                },
                "action_worker/4": {
                    "result": {
                        "import": "account",
                        "rows": [
                            {
                                "state": ImportState.ERROR,
                                "error": ["test"],
                                "data": {"gender": "male"},
                            },
                        ],
                    },
                },
                "action_worker/5": {"result": None},
            }
        )

    def test_import_username_and_create(self) -> None:
        response = self.request("user.import", {"id": 2, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"username": "test", "first_name": "Testy"},
        )
        self.assert_model_not_exists("action_worker/2")

    def test_import_abort(self) -> None:
        response = self.request("user.import", {"id": 2, "import": False})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("action_worker/2")
        self.assert_model_not_exists("user/2")

    def test_import_wrong_action_worker(self) -> None:
        response = self.request("user.import", {"id": 5, "import": True})
        self.assert_status_code(response, 400)
        assert (
            "Wrong id doesn't point on account import data." in response.json["message"]
        )

    def test_import_username_and_update(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "username": "test",
                },
                "action_worker/6": {
                    "result": {
                        "import": "account",
                        "rows": [
                            {
                                "state": ImportState.DONE,
                                "error": [],
                                "data": {
                                    "username": {
                                        "value": "test",
                                        "info": ImportState.DONE,
                                    },
                                    "id": 1,
                                    "first_name": "Testy",
                                },
                            },
                        ],
                    },
                },
            }
        )
        response = self.request("user.import", {"id": 6, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/2")
        self.assert_model_exists("user/1", {"first_name": "Testy"})

    def test_import_names_and_email_and_create(self) -> None:
        response = self.request("user.import", {"id": 3, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "TestyTester",
                "first_name": "Testy",
                "gender": "male",
                "last_name": "Tester",
                "email": "email@test.com",
            },
        )

    def test_import_error_state(self) -> None:
        response = self.request("user.import", {"id": 4, "import": True})
        self.assert_status_code(response, 400)
        assert "Error in import." in response.json["message"]

    def test_import_no_permission(self) -> None:
        self.base_permission_test({}, "user.import", {"id": 2, "import": True})

    def test_import_permission(self) -> None:
        self.base_permission_test(
            {},
            "user.import",
            {"id": 2, "import": True},
            OrganizationManagementLevel.CAN_MANAGE_USERS,
        )
