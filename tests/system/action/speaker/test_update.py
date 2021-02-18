from tests.system.action.base import BaseActionTestCase


class SpeakerSystemTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models(
            {
                "user/7": {"username": "test_username1"},
                "list_of_speakers/23": {"speaker_ids": [890]},
                "speaker/890": {"user_id": 7, "list_of_speakers_id": 23},
            }
        )
        response = self.request("speaker.update", {"id": 890, "marked": True})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("marked") is True

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "user/7": {"username": "test_username1"},
                "list_of_speakers/23": {"speaker_ids": [890]},
                "speaker/890": {"user_id": 7, "list_of_speakers_id": 23},
            }
        )
        response = self.request("speaker.update", {"id": 889, "marked": True})
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        assert model.get("marked") is None
