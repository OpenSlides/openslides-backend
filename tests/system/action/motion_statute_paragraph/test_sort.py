from tests.system.action.base import BaseActionTestCase


class MotionStatuteParagraphSortActionTest(BaseActionTestCase):
    def test_sort_correct_1(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_statute_paragraph/31", {"meeting_id": 222, "title": "title_loisueb"}
        )
        self.create_model(
            "motion_statute_paragraph/32",
            {"meeting_id": 222, "title": "title_blanumop"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_statute_paragraph.sort",
                    "data": [{"meeting_id": 222, "statute_paragraph_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model_31 = self.get_model("motion_statute_paragraph/31")
        assert model_31.get("weight") == 2
        model_32 = self.get_model("motion_statute_paragraph/32")
        assert model_32.get("weight") == 1

    def test_sort_missing_model(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_statute_paragraph/31", {"meeting_id": 222, "title": "title_loisueb"}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_statute_paragraph.sort",
                    "data": [{"meeting_id": 222, "statute_paragraph_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Id 32 not in db_instances." in str(response.data)

    def test_sort_another_section_db(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_statute_paragraph/31", {"meeting_id": 222, "title": "title_loisueb"}
        )
        self.create_model(
            "motion_statute_paragraph/32",
            {"meeting_id": 222, "title": "title_blanumop"},
        )
        self.create_model(
            "motion_statute_paragraph/33",
            {"meeting_id": 222, "title": "title_polusiem"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_statute_paragraph.sort",
                    "data": [{"meeting_id": 222, "statute_paragraph_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Additional db_instances found." in str(response.data)
