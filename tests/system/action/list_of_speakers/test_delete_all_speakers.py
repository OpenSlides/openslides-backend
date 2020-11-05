from tests.system.action.base import BaseActionTestCase


class ListOfSpeakersDeleteAllSpeakersActionTester(BaseActionTestCase):
    def test_delete_all_correct(self) -> None:
        self.create_model("meeting/222", {"name": "name_xQyvfmsS"})
        self.create_model(
            "list_of_speakers/111",
            {"closed": False, "meeting_id": 222, "speaker_ids": list(range(1, 11))},
        )
        for i in range(1, 11):
            self.create_model(f"speaker/{i}", {"list_of_speakers_id": 111})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "list_of_speakers.delete_all_speakers",
                    "data": [{"id": 111}],
                }
            ],
        )
        self.assert_status_code(response, 200)

        for i in range(1, 11):
            self.assert_model_deleted(f"speaker/{i}")

    def test_wrong_id(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "list_of_speakers.delete_all_speakers",
                    "data": [{"id": 111}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertTrue(
            "Model \\'list_of_speakers/111\\' does not exist." in str(response.data)
        )
