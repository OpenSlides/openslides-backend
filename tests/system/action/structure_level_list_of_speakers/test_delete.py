from tests.system.action.base import BaseActionTestCase


class StructureLevelListOfSpeakersDeleteTest(BaseActionTestCase):
    def test_delete(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_default_structure_level_time": 600,
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
                },
            }
        )
        self.request("structure_level_list_of_speakers.delete", {"id": 3})
        self.assert_model_not_exists("structure_level_list_of_speakers/3")
        self.assert_model_exists(
            "meeting/1",
            {
                "structure_level_list_of_speakers_ids": [],
            },
        )
        self.assert_model_exists(
            "structure_level/1",
            {
                "structure_level_list_of_speakers_ids": [],
            },
        )
        self.assert_model_exists(
            "list_of_speakers/2",
            {
                "structure_level_list_of_speakers_ids": [],
            },
        )
