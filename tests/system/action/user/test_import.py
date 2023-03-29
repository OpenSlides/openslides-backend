from openslides_backend.action.actions.user.json_upload import ImportStatus
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
                                "status": ImportStatus.NEW,
                                "error": [],
                                "data": {"username": "test"},
                            },
                            {
                                "status": ImportStatus.ERROR,
                                "error": ["test"],
                                "data": {"username": "broken"},
                            },
                        ],
                    }
                },
            }
        )

    def test_import_correct(self) -> None:
        response = self.request("user.import", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "test"})

    def test_import_duplicates_in_db(self) -> None:
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
