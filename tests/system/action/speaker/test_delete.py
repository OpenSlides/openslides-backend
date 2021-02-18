from tests.system.action.base import BaseActionTestCase


class SpeakerDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/111": {"speaker_ids": [890]},
                "user/7": {
                    "username": "test_username1",
                    "speaker_$111_ids": [890],
                    "speaker_$_ids": ["111"],
                },
                "list_of_speakers/23": {"speaker_ids": [890]},
                "speaker/890": {
                    "user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 111,
                },
            }
        )
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/890")
        user = self.get_model("user/7")
        assert user.get("speaker_$111_ids") == []
        assert user.get("speaker_$_ids") == []

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/111": {"speaker_ids": [890]},
                "user/7": {
                    "username": "test_username1",
                    "speaker_$111_ids": [890],
                    "speaker_$_ids": ["111"],
                },
                "list_of_speakers/23": {"speaker_ids": [890]},
                "speaker/890": {
                    "user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 111,
                },
            }
        )
        response = self.request("speaker.delete", {"id": 889})
        self.assert_status_code(response, 400)
        self.assert_model_exists("speaker/890")
