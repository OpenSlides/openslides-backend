from tests.system.action.base import BaseActionTestCase


class MeetingDeleteAllSpeakersOfAllListsActionTest(BaseActionTestCase):
    def test_no_los(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_srtgb123", "list_of_speakers_ids": []}
        )
        response = self.request("meeting.delete_all_speakers_of_all_lists", {"id": 110})
        self.assert_status_code(response, 200)

    def test_one_los_empty(self) -> None:
        self.set_models(
            {
                "list_of_speakers/11": {"meeting_id": 110, "speaker_ids": []},
                "meeting/110": {"name": "name_srtgb123", "list_of_speakers_ids": [11]},
            }
        )
        response = self.request("meeting.delete_all_speakers_of_all_lists", {"id": 110})
        self.assert_status_code(response, 200)

    def test_1_los_1_speaker(self) -> None:
        self.set_models(
            {
                "list_of_speakers/11": {"meeting_id": 110, "speaker_ids": [1]},
                "speaker/1": {"list_of_speakers_id": 11, "meeting_id": 110},
                "meeting/110": {
                    "name": "name_srtgb123",
                    "list_of_speakers_ids": [11],
                    "speaker_ids": [1],
                },
            }
        )
        response = self.request("meeting.delete_all_speakers_of_all_lists", {"id": 110})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/1")

    def test_1_los_2_speakers(self) -> None:
        self.set_models(
            {
                "list_of_speakers/11": {"meeting_id": 110, "speaker_ids": [1, 2]},
                "speaker/1": {"list_of_speakers_id": 11, "meeting_id": 110},
                "speaker/2": {"list_of_speakers_id": 11, "meeting_id": 110},
                "meeting/110": {
                    "name": "name_srtgb123",
                    "list_of_speakers_ids": [11],
                    "speaker_ids": [1, 2],
                },
            }
        )
        response = self.request("meeting.delete_all_speakers_of_all_lists", {"id": 110})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/1")
        self.assert_model_deleted("speaker/2")

    def test_3_los(self) -> None:
        self.set_models(
            {
                "list_of_speakers/11": {"meeting_id": 110, "speaker_ids": [1, 2]},
                "speaker/1": {"list_of_speakers_id": 11, "meeting_id": 110},
                "speaker/2": {"list_of_speakers_id": 11, "meeting_id": 110},
                "list_of_speakers/12": {"meeting_id": 110, "speaker_ids": []},
                "list_of_speakers/13": {"meeting_id": 110, "speaker_ids": [3]},
                "speaker/3": {"list_of_speakers_id": 13, "meeting_id": 110},
                "meeting/110": {
                    "name": "name_srtgb123",
                    "list_of_speakers_ids": [11, 12, 13],
                    "speaker_ids": [1, 2, 3],
                },
            }
        )

        response = self.request("meeting.delete_all_speakers_of_all_lists", {"id": 110})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/1")
        self.assert_model_deleted("speaker/2")
        self.assert_model_deleted("speaker/3")
