from openslides_backend.shared.exceptions import DatabaseException
from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class MotionStatuteParagraphActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model(
            get_fqid("motion_statute_paragraph/111"), {"title": "title_srtgb123"}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_statute_paragraph.update",
                    "data": [{"id": 111, "title": "title_Xcdfgee"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("motion_statute_paragraph/111"))
        model = self.datastore.get(get_fqid("motion_statute_paragraph/111"))
        assert model.get("title") == "title_Xcdfgee"

    def test_update_wrong_id(self) -> None:
        self.create_model(
            get_fqid("motion_statute_paragraph/111"), {"title": "title_srtgb123"}
        )
        with self.assertRaises(DatabaseException):
            self.client.post(
                "/",
                json=[
                    {
                        "action": "motion_statute_paragraph.update",
                        "data": [{"id": 112, "title": "title_Xcdfgee"}],
                    }
                ],
            )
        model = self.datastore.get(get_fqid("motion_statute_paragraph/111"))
        assert model.get("title") == "title_srtgb123"
