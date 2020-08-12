from openslides_backend.shared.exceptions import DatabaseException
from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class MotionChangeRecommendationActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model(
            get_fqid("motion/25"),
            {"title": "title_pheK0Ja3ai", "statute_paragraph_id": None},
        )
        self.create_model(
            get_fqid("motion_change_recommendation/111"),
            {"line_from": 11, "line_to": 23, "text": "text_LhmrbbwS", "motion_id": 25},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_change_recommendation.update",
                    "data": [
                        {
                            "id": 111,
                            "text": "text_zzTWoMte",
                            "rejected": False,
                            "internal": True,
                            "type": 1,
                            "other_description": "other_description_IClpabuM",
                        }
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("motion_change_recommendation/111"))
        model = self.datastore.get(get_fqid("motion_change_recommendation/111"))

        assert model.get("text") == "text_zzTWoMte"
        assert model.get("rejected") is False
        assert model.get("internal") is True
        assert model.get("type") == 1
        assert model.get("other_description") == "other_description_IClpabuM"

    def test_update_wrong_id(self) -> None:
        self.create_model(
            get_fqid("motion/25"),
            {"title": "title_pheK0Ja3ai", "statute_paragraph_id": None},
        )
        self.create_model(
            get_fqid("motion_change_recommendation/111"),
            {"line_from": 11, "line_to": 23, "text": "text_LhmrbbwS", "motion_id": 25},
        )
        with self.assertRaises(DatabaseException):
            self.client.post(
                "/",
                json=[
                    {
                        "action": "motion_change_recommendation.update",
                        "data": [{"id": 112, "text": "text_Xcdfgee"}],
                    }
                ],
            )
        model = self.datastore.get(get_fqid("motion_change_recommendation/111"))
        assert model.get("text") == "text_LhmrbbwS"
        assert model.get("line_from") == 11
        assert model.get("line_to") == 23
        assert model.get("motion_id") == 25
