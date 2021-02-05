from tests.system.action.base import BaseActionTestCase


class AssignmentDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("assignment/111", {"title": "title_srtgb123"})
        response = self.request("assignment.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("assignment/111")

    def test_delete_correct_cascading(self) -> None:
        self.set_models(
            {
                "assignment/111": {
                    "list_of_speakers_id": 222,
                    "agenda_item_id": 333,
                },
                "list_of_speakers/222": {
                    "closed": False,
                    "content_object_id": "assignment/111",
                },
                "agenda_item/333": {
                    "comment": "test_comment_ewoirzewoirioewr",
                    "content_object_id": "assignment/111",
                },
            }
        )
        response = self.request("assignment.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("assignment/111")
        self.assert_model_deleted("agenda_item/333")
        self.assert_model_deleted("list_of_speakers/222")

    def test_delete_wrong_id(self) -> None:
        self.create_model("assignment/112", {"title": "title_srtgb123"})
        response = self.request("assignment.delete", {"id": 111})
        self.assert_status_code(response, 400)
        model = self.get_model("assignment/112")
        self.assertEqual(model.get("title"), "title_srtgb123")
