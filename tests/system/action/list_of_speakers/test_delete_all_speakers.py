from tests.system.action.base import BaseActionTestCase


class ListOfSpeakersDeleteAllSpeakersActionTester(BaseActionTestCase):
    def test_delete_all_correct(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_xQyvfmsS",
                    "speaker_ids": list(range(1, 11)),
                },
                "list_of_speakers/111": {
                    "closed": False,
                    "meeting_id": 222,
                    "speaker_ids": list(range(1, 11)),
                },
            }
        )
        for i in range(1, 11):
            self.create_model(
                f"speaker/{i}", {"list_of_speakers_id": 111, "meeting_id": 222}
            )
        response = self.request("list_of_speakers.delete_all_speakers", {"id": 111})
        self.assert_status_code(response, 200)

        for i in range(1, 11):
            self.assert_model_deleted(f"speaker/{i}")

    def test_wrong_id(self) -> None:
        response = self.request("list_of_speakers.delete_all_speakers", {"id": 111})
        self.assert_status_code(response, 400)
        self.assertTrue(
            "Model 'list_of_speakers/111' does not exist." in response.json["message"]
        )
