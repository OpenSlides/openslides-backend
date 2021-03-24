from tests.system.action.base import BaseActionTestCase


class MotionBlockActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models({"meeting/11": {}, "motion_block/111": {"meeting_id": 11}})
        response = self.request("motion_block.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_block/111")

    def test_delete_wrong_id(self) -> None:
        self.set_models({"meeting/11": {}, "motion_block/112": {"meeting_id": 11}})
        response = self.request("motion_block.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_block/112")

    def test_delete_correct_cascading(self) -> None:
        self.set_models(
            {
                "meeting/12": {},
                "motion_block/111": {
                    "list_of_speakers_id": 222,
                    "agenda_item_id": 333,
                    "meeting_id": 12,
                },
                "list_of_speakers/222": {
                    "closed": False,
                    "content_object_id": "motion_block/111",
                    "meeting_id": 12,
                },
                "agenda_item/333": {
                    "comment": "test_comment_ewoirzewoirioewr",
                    "content_object_id": "motion_block/111",
                    "meeting_id": 12,
                },
            }
        )
        response = self.request("motion_block.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_block/111")
        self.assert_model_deleted("agenda_item/333")
        self.assert_model_deleted("list_of_speakers/222")

    def test_permissions(self) -> None:
        self.base_permission_test(
            {"meeting/11": {}, "motion_block/111": {"meeting_id": 11}},
            "motion_block.delete",
            {"id": 111},
        )
