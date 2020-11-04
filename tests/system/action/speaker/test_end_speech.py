from tests.system.action.base import BaseActionTestCase


class SpeakerEndSpeachTester(BaseActionTestCase):
    def test_correct(self) -> None:
        self.create_model("user/7", {"username": "test_username1"})
        self.create_model("list_of_speakers/23", {"speaker_ids": [890]})
        self.create_model(
            "speaker/890",
            {"user_id": 7, "list_of_speakers_id": 23, "begin_time": 10000},
        )
        response = self.client.post(
            "/",
            json=[{"action": "speaker.end_speech", "data": [{"id": 890}]}],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        self.assertTrue(model.get("end_time") is not None)

    def test_wrong_id(self) -> None:
        self.create_model("user/7", {"username": "test_username1"})
        self.create_model("list_of_speakers/23", {"speaker_ids": [890]})
        self.create_model(
            "speaker/890",
            {"user_id": 7, "list_of_speakers_id": 23, "begin_time": 10000},
        )
        response = self.client.post(
            "/",
            json=[{"action": "speaker.end_speech", "data": [{"id": 889}]}],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        self.assertTrue(model.get("end_time") is None)
        self.assertTrue("Model \\'speaker/889\\' does not exist." in str(response.data))

    def test_existing_speaker(self) -> None:
        self.create_model("user/7", {"username": "test_username1"})
        self.create_model("list_of_speakers/23", {"speaker_ids": [890]})
        self.create_model(
            "speaker/890",
            {
                "user_id": 7,
                "list_of_speakers_id": 23,
                "begin_time": 100000,
                "end_time": 200000,
            },
        )
        response = self.client.post(
            "/",
            json=[{"action": "speaker.end_speech", "data": [{"id": 890}]}],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        self.assertEqual(model.get("begin_time"), 100000)
        self.assertEqual(model.get("end_time"), 200000)
        self.assertTrue(
            "Speaker 890 is not speaking at the moment." in str(response.data)
        )

    def test_existing_speaker_2(self) -> None:
        self.create_model("user/7", {"username": "test_username1"})
        self.create_model("list_of_speakers/23", {"speaker_ids": [890]})
        self.create_model(
            "speaker/890",
            {"user_id": 7, "list_of_speakers_id": 23},
        )
        response = self.client.post(
            "/",
            json=[{"action": "speaker.end_speech", "data": [{"id": 890}]}],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        self.assertTrue(model.get("begin_time") is None)
        self.assertTrue(model.get("end_time") is None)
        self.assertTrue(
            "Speaker 890 is not speaking at the moment." in str(response.data)
        )
