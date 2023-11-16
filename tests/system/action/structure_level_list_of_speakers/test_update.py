from time import time

from tests.system.action.base import BaseActionTestCase


class StructureLevelListOfSpeakersUpdateTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {
                    "is_active_in_organization_id": 1,
                    "structure_level_ids": [1],
                    "list_of_speakers_ids": [2],
                    "structure_level_list_of_speakers_ids": [3],
                },
                "structure_level/1": {
                    "meeting_id": 1,
                    "structure_level_list_of_speakers_ids": [3],
                },
                "list_of_speakers/2": {
                    "meeting_id": 1,
                    "structure_level_list_of_speakers_ids": [3],
                },
                "structure_level_list_of_speakers/3": {
                    "structure_level_id": 1,
                    "list_of_speakers_id": 2,
                    "meeting_id": 1,
                    "initial_time": 600,
                    "remaining_time": 500,
                },
            }
        )

    def test_set_start_time(self) -> None:
        now = round(time())
        response = self.request(
            "structure_level_list_of_speakers.update",
            {"id": 3, "current_start_time": now},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/3",
            {
                "initial_time": 600,
                "remaining_time": 500,
                "current_start_time": now,
            },
        )

    def test_set_spoken_time(self) -> None:
        self.set_models(
            {
                "structure_level_list_of_speakers/3": {
                    "current_start_time": round(time())
                }
            }
        )
        response = self.request(
            "structure_level_list_of_speakers.update",
            {"id": 3, "current_start_time": None, "spoken_time": 100},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/3",
            {
                "initial_time": 600,
                "remaining_time": 400,
                "current_start_time": None,
            },
        )
