from openslides_backend.action.actions.user.json_upload import ImportStatus
from tests.system.action.base import BaseActionTestCase


class TopicJsonUpload(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/22": {"name": "test", "is_active_in_organization_id": 1},
            }
        )

    def test_json_upload(self) -> None:
        response = self.request(
            "user.json_upload",
            {
                "data": [
                    {
                        "username": "test",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "status": ImportStatus.NEW,
            "error": [],
            "data": {
                "username": "test",
            },
        }

    def test_json_upload_wrong_data(self) -> None:
        response = self.request(
            "user.json_upload",
            {"data": [{"username": "test", "wrong": 15}]},
        )
        self.assert_status_code(response, 400)
        assert (
            "data.data[0] must not contain {'wrong'} properties"
            in response.json["message"]
        )

    def test_json_upload_empty_data(self) -> None:
        response = self.request(
            "user.json_upload",
            {"data": []},
        )
        self.assert_status_code(response, 400)
        assert "data.data must contain at least 1 items" in response.json["message"]

    def test_json_upload_results(self) -> None:
        response = self.request(
            "user.json_upload",
            {"data": [{"username": "test"}]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "action_worker/1",
            {
                "result": {
                    "import": "account",
                    "rows": [
                        {
                            "status": ImportStatus.NEW,
                            "error": [],
                            "data": {"username": "test"},
                        }
                    ],
                }
            },
        )
        result = response.json["results"][0][0]
        assert result == {
            "id": 1,
            "headers": [
                {"property": "title", "type": "string"},
                {"property": "first_name", "type": "string"},
                {"property": "last_name", "type": "string"},
                {"property": "is_active", "type": "boolean"},
                {"property": "is_physical_person", "type": "boolean"},
                {"property": "default_password", "type": "string"},
                {"property": "email", "type": "string"},
                {"property": "username", "type": "string"},
                {"property": "gender", "type": "string"},
                {"property": "pronoun", "type": "string"},
            ],
            "rows": [
                {
                    "status": ImportStatus.NEW,
                    "error": [],
                    "data": {
                        "username": "test",
                    },
                }
            ],
            "statistics": {"total": 1, "created": 1, "omitted": 0},
        }

    def test_json_upload_duplicate_in_db(self) -> None:
        self.set_models(
            {
                "user/3": {"username": "test"},
            }
        )
        response = self.request(
            "user.json_upload",
            {"data": [{"username": "test"}]},
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["rows"] == [
            {
                "status": ImportStatus.ERROR,
                "error": ["Duplicate"],
                "data": {"username": "test"},
            }
        ]

    def test_json_upload_duplicate_in_data(self) -> None:
        response = self.request(
            "user.json_upload",
            {
                "data": [
                    {"username": "test"},
                    {"username": "bla"},
                    {"username": "test"},
                ],
            },
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["rows"][2]["error"] == ["Duplicate"]
        assert result["rows"][2]["status"] == ImportStatus.ERROR
        self.assert_model_exists(
            "action_worker/1",
            {
                "result": {
                    "import": "account",
                    "rows": [
                        {
                            "status": ImportStatus.NEW,
                            "error": [],
                            "data": {"username": "test"},
                        },
                        {
                            "status": ImportStatus.NEW,
                            "error": [],
                            "data": {"username": "bla"},
                        },
                        {
                            "status": ImportStatus.ERROR,
                            "error": ["Duplicate"],
                            "data": {"username": "test"},
                        },
                    ],
                }
            },
        )

    # def test_json_upload_no_permission(self) -> None:
    #    self.base_permission_test(
    #        {}, "user.json_upload", {"data": [{"username": "test"}]}
    #    )

    # def test_json_upload_permission(self) -> None:
    #    self.base_permission_test(
    #        {},
    #        "user.json_upload",
    #        {"data": [{"username": "test"}]},
    #        Permissions.AgendaItem.CAN_MANAGE,
    #    )
