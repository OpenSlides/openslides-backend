from tests.system.action.base import BaseActionTestCase


class MotionCommentCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("meeting/111", {"name": "name_m123etrd"})
        self.create_model("motion/357", {"title": "title_YIDYXmKj", "meeting_id": 111})
        self.create_model("motion_comment_section/78", {"meeting_id": 111})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_comment.create",
                    "data": [
                        {"comment": "test_Xcdfgee", "motion_id": 357, "section_id": 78}
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_comment/1")
        assert model.get("comment") == "test_Xcdfgee"
        assert model.get("motion_id") == 357
        assert model.get("section_id") == 78

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/",
            json=[{"action": "motion_comment.create", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['comment', 'motion_id', 'section_id'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        self.create_model("meeting/111", {"name": "name_m123etrd"})
        self.create_model("motion/357", {"title": "title_YIDYXmKj", "meeting_id": 111})
        self.create_model("motion_comment_section/78", {})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_comment.create",
                    "data": [
                        {
                            "comment": "test_Xcdfgee",
                            "motion_id": 357,
                            "section_id": 78,
                            "wrong_field": "text_AefohteiF8",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )
