from tests.system.action.base import BaseActionTestCase


class StructureLevelListOfSpeakersDeleteTest(BaseActionTestCase):
    def test_delete(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_default_structure_level_time": 600,
                },
                "topic/32": {
                    "title": "leet improvement discussion",
                    "sequential_number": 32,
                    "meeting_id": 1,
                },
                "structure_level/1": {
                    "name": "monkey",
                    "meeting_id": 1,
                    "structure_level_list_of_speakers_ids": [3],
                },
                "list_of_speakers/2": {
                    "meeting_id": 1,
                    "sequential_number": 2,
                    "content_object_id": "topic/32",
                    "structure_level_list_of_speakers_ids": [3],
                },
                "structure_level_list_of_speakers/3": {
                    "structure_level_id": 1,
                    "list_of_speakers_id": 2,
                    "initial_time": 400,
                    "remaining_time": 300,
                    "meeting_id": 1,
                },
            }
        )
        self.request("structure_level_list_of_speakers.delete", {"id": 3})
        self.assert_model_not_exists("structure_level_list_of_speakers/3")
        self.assert_model_exists(
            "meeting/1",
            {
                "structure_level_list_of_speakers_ids": None,
            },
        )
        self.assert_model_exists(
            "structure_level/1",
            {
                "structure_level_list_of_speakers_ids": None,
            },
        )
        self.assert_model_exists(
            "list_of_speakers/2",
            {
                "structure_level_list_of_speakers_ids": None,
            },
        )
