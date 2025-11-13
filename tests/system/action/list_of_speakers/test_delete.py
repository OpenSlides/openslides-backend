from tests.system.action.base import BaseActionTestCase


class ListOfSpeakersDeleteActionTest(BaseActionTestCase):
    """
    This action is backend internal and can only successfully be called by the content objects delete action.
    Correct deletion shall be assured through tests of the possible content objects.
    Since in this example topic has the reference required and is not deleted cascadingly
    it's not possible to test successful deletion directly.
    """

    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(78)
        self.set_models(
            {
                "topic/42": {
                    "title": "leet improvement discussion",
                    "meeting_id": 78,
                },
                "agenda_item/23": {"content_object_id": "topic/42", "meeting_id": 78},
                "list_of_speakers/111": {
                    "content_object_id": "topic/42",
                    "closed": True,
                    "meeting_id": 78,
                },
                "projection/1": {
                    "content_object_id": "list_of_speakers/111",
                    "current_projector_id": 1,
                    "meeting_id": 78,
                },
                "projector/1": {
                    "meeting_id": 78,
                },
            }
        )

    def test_delete_indirectly(self) -> None:
        response = self.request("topic.delete", {"id": 42})

        self.assert_status_code(response, 200)
        self.assert_model_not_exists("list_of_speakers/111")
        self.assert_model_not_exists("projection/1")
        self.assert_model_not_exists("topic/42")

    def test_delete_correct_id(self) -> None:
        response = self.request("list_of_speakers.delete", {"id": 111})

        self.assert_status_code(response, 400)
        self.assertIn(
            "Relation violates required constraint: Trigger tr_ud_topic_list_of_speakers_id: NOT NULL CONSTRAINT VIOLATED for topic/42/list_of_speakers_id from relationship before 111/content_object_id_topic_id",
            response.json["message"],
        )
        self.assert_model_exists("list_of_speakers/111")
        self.assert_model_exists("projection/1")
        self.assert_model_exists("topic/42")

    def test_delete_wrong_id(self) -> None:
        response = self.request("list_of_speakers.delete", {"id": 112})
        self.assert_status_code(response, 400)
        self.assert_model_exists(
            "list_of_speakers/111", {"closed": True, "meeting_id": 78}
        )
