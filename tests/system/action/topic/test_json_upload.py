from openslides_backend.permissions.permissions import Permissions
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
            "topic.json_upload",
            {"meeting_id": 22, "data": [{"title": "test"}]},
        )
        self.assert_status_code(response, 200)

    def test_json_upload_agenda_data(self) -> None:
        response = self.request(
            "topic.json_upload",
            {
                "meeting_id": 22,
                "data": [
                    {
                        "title": "test",
                        "agenda_comment": "testtesttest",
                        "agenda_type": "hidden",
                        "agenda_duration": 50,
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "status": "new",
            "error": [],
            "data": {
                "title": "test",
                "meeting_id": 22,
                "agenda_comment": "testtesttest",
                "agenda_type": "hidden",
                "agenda_duration": 50,
            },
        }

    def test_json_upload_wrong_data(self) -> None:
        response = self.request(
            "topic.json_upload",
            {"meeting_id": 22, "data": [{"title": "test", "wrong": 15}]},
        )
        self.assert_status_code(response, 400)
        assert (
            "data.data[0] must not contain {'wrong'} properties"
            in response.json["message"]
        )

    def test_json_upload_empty_data(self) -> None:
        response = self.request(
            "topic.json_upload",
            {"meeting_id": 22, "data": []},
        )
        self.assert_status_code(response, 400)
        assert "data.data must contain at least 1 items" in response.json["message"]

    def test_json_upload_results(self) -> None:
        response = self.request(
            "topic.json_upload",
            {"meeting_id": 22, "data": [{"title": "test"}]},
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["id"] == 1
        self.assert_model_exists(
            "action_worker/1",
            {
                "result": [
                    {
                        "status": "new",
                        "error": [],
                        "data": {"title": "test", "meeting_id": 22},
                    }
                ]
            },
        )
        assert result["headers"][0] == {
            "property": "title",
            "type": "string",
        }
        assert result["rows"][0] == {
            "status": "new",
            "error": [],
            "data": {"title": "test", "meeting_id": 22},
        }
        assert result["statistics"] == {"itemCount": 1, "Created": 1, "Error": 0}

    def test_json_upload_no_permission(self) -> None:
        self.base_permission_test(
            {}, "topic.json_upload", {"data": [{"title": "test"}], "meeting_id": 1}
        )

    def test_json_uplad_permission(self) -> None:
        self.base_permission_test(
            {},
            "topic.json_upload",
            {"data": [{"title": "test"}], "meeting_id": 1},
            Permissions.AgendaItem.CAN_MANAGE,
        )
