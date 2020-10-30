from tests.system.action.base import BaseActionTestCase


class SpeakerCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("meeting/7844", {"name": "name_asdewqasd"})
        self.create_model("user/7", {"username": "test_username1", "speakers_id": []})
        self.create_model(
            "list_of_speakers/23", {"speaker_ids": [], "meeting_id": 7844}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "speaker.create",
                    "data": [{"user_id": 7, "list_of_speakers_id": 23}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        speaker = self.get_model("speaker/1")
        assert speaker.get("user_id") == 7
        assert speaker.get("list_of_speakers_id") == 23
        assert speaker.get("weight") == 10000
        list_of_speakers = self.get_model("list_of_speakers/23")
        assert list_of_speakers.get("speaker_ids") == [1]

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/",
            json=[{"action": "speaker.create", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'list_of_speakers_id\\', \\'user_id\\'] properties",
            str(response.data),
        )

    def test_create_wrong_field(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "speaker.create",
                    "data": [{"wrong_field": "text_AefohteiF8"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'list_of_speakers_id\\', \\'user_id\\'] properties",
            str(response.data),
        )
