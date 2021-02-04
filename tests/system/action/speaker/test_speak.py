from tests.system.action.base import BaseActionTestCase


class SpeakerSpeakTester(BaseActionTestCase):
    def test_speak_correct(self) -> None:
        self.create_model("user/7", {"username": "test_username1"})
        self.create_model("list_of_speakers/23", {"speaker_ids": [890]})
        self.create_model("speaker/890", {"user_id": 7, "list_of_speakers_id": 23})
        response = self.client.post(
            "/",
            json=[{"action": "speaker.speak", "data": [{"id": 890}]}],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        self.assertTrue(model.get("begin_time") is not None)

    def test_speak_wrong_id(self) -> None:
        self.create_model("user/7", {"username": "test_username1"})
        self.create_model("list_of_speakers/23", {"speaker_ids": [890]})
        self.create_model("speaker/890", {"user_id": 7, "list_of_speakers_id": 23})
        response = self.client.post(
            "/",
            json=[{"action": "speaker.speak", "data": [{"id": 889}]}],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        self.assertTrue(model.get("begin_time") is None)

    def test_speak_existing_speaker(self) -> None:
        self.create_model("user/7", {"username": "test_username1"})
        self.create_model("list_of_speakers/23", {"speaker_ids": [890]})
        self.create_model(
            "speaker/890",
            {"user_id": 7, "list_of_speakers_id": 23, "begin_time": 100000},
        )
        response = self.client.post(
            "/",
            json=[{"action": "speaker.speak", "data": [{"id": 890}]}],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        self.assertEqual(model.get("begin_time"), 100000)

    def test_speak_next_speaker(self) -> None:
        self.create_model("user/7", {"username": "test_username1"})
        self.create_model("list_of_speakers/23", {"speaker_ids": [890, 891]})
        self.create_model(
            "speaker/890",
            {"user_id": 7, "list_of_speakers_id": 23, "begin_time": 100000},
        )
        self.create_model("speaker/891", {"user_id": 7, "list_of_speakers_id": 23})

        response = self.client.post(
            "/",
            json=[{"action": "speaker.speak", "data": [{"id": 891}]}],
        )
        self.assert_status_code(response, 200)
        model2 = self.get_model("speaker/891")
        self.assertTrue(model2.get("begin_time") is not None)
        model1 = self.get_model("speaker/890")
        self.assertEqual(model1.get("end_time"), model2["begin_time"])

    def test_closed(self) -> None:
        self.create_model("user/7", {"username": "test_username1"})
        self.create_model("list_of_speakers/23", {"speaker_ids": [890], "closed": True})
        self.create_model("speaker/890", {"user_id": 7, "list_of_speakers_id": 23})
        response = self.client.post(
            "/",
            json=[{"action": "speaker.speak", "data": [{"id": 890}]}],
        )
        self.assert_status_code(response, 400)
        self.assertTrue(
            "The list of speakers is closed." in response.json.get("message", "")
        )
