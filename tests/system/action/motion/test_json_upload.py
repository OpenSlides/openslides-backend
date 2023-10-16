from openslides_backend.action.mixins.import_mixins import ImportState
from tests.system.action.base import BaseActionTestCase


class MotionJsonUpload(BaseActionTestCase):
    def test_json_upload_simple(self) -> None:
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "text": "my", "reason": "stuff"}],
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "title": {"value": "test", "info": ImportState.DONE},
                "text": {"value": "my", "info": ImportState.DONE},
                "reason": {"value": "stuff", "info": ImportState.DONE},
            },
        }

    def test_json_upload_empty_data(self) -> None:
        response = self.request(
            "motion.json_upload",
            {"data": []},
        )
        self.assert_status_code(response, 400)
        assert "data.data must contain at least 2 items" in response.json["message"]
