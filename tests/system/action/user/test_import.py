from openslides_backend.action.actions.user.json_upload import ImportStatus
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
                                "status": ImportStatus.CREATE,
                                "error": [],
                                "data": {"username": "test", "first_name": "Testy"},
                            },
                        ],
                    },
                },
                "action_worker/3": {
                    "result": {
                        "import": "account",
                        "rows": [
                            {
                                "status": ImportStatus.CREATE,
                                "error": [],
                                "data": {"first_name": "Testy", "gender": "male"},
                            },
                        ],
                    },
                },
                "action_worker/4": {
                    "result": {
                        "import": "account",
                        "rows": [
                            {
                                "status": ImportStatus.ERROR,
                                "error": ["test"],
                                "data": {"gender": "male"},
                            },
                        ],
                    },
                },
            }
        )

    def test_import_username_and_create(self) -> None:
        response = self.request("user.import", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "test", "first_name": "Testy"})

    def test_import_username_and_update(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "username": "test",
                },
            }
        )
        response = self.request("user.import", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/2")
        self.assert_model_exists("user/1", {"first_name": "Testy"})

    def test_import_names_and_email_and_create(self) -> None:
        response = self.request("user.import", {"id": 3})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2", {"username": "Testy", "first_name": "Testy", "gender": "male"}
        )

    def test_import_names_and_email_and_update(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "username": "test",
                    "first_name": "Testy",
                },
            }
        )
        response = self.request("user.import", {"id": 3})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("user/2")
        self.assert_model_exists("user/1", {"first_name": "Testy", "gender": "male"})

    def test_import_error_status(self) -> None:
        response = self.request("user.import", {"id": 4})
        self.assert_status_code(response, 400)
        assert "Error in import." in response.json["message"]

    def test_import_no_permission(self) -> None:
        self.base_permission_test({}, "user.import", {"id": 2})

    def test_import_permission(self) -> None:
        self.base_permission_test(
            {},
            "user.import",
            {"id": 2},
            OrganizationManagementLevel.CAN_MANAGE_USERS,
        )
