from tests.system.action.base import BaseActionTestCase


class ListOfSpeakersDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_meeting(78)
        self.set_models(
            {
                "topic/42": {
                    "title": "leet improvement discussion",
                    "sequential_number": 42,
                    "meeting_id": 78,
                },
                "list_of_speakers/111": {
                    "content_object_id": "topic/42",
                    "sequential_number": 10,
                    "closed": True,
                    "meeting_id": 78,
                },
                "projection/1": {
                    "content_object_id": "list_of_speakers/111",
                    "current_projector_id": 1,
                    "meeting_id": 78,
                },
                "projector/1": {
                    "sequential_number": 1,
                    "meeting_id": 78,
                },
            }
        )
        response = self.request("list_of_speakers.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_not_exists("list_of_speakers/111")
        self.assert_model_not_exists("projection/1")
        self.assert_model_not_exists("topic/42")

    def test_delete_wrong_id(self) -> None:
        self.create_meeting(78)
        self.set_models(
            {
                "topic/42": {
                    "title": "leet improvement discussion",
                    "sequential_number": 42,
                    "meeting_id": 78,
                },
                "list_of_speakers/112": {
                    "content_object_id": "topic/42",
                    "sequential_number": 10,
                    "closed": True,
                    "meeting_id": 78,
                },
            }
        )
        response = self.request("list_of_speakers.delete", {"id": 111})
        self.assert_status_code(response, 400)
        model = self.get_model("list_of_speakers/112")
        assert model.get("closed") is True
        assert model.get("meeting_id") == 78
