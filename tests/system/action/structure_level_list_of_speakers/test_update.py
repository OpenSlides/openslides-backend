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
                    "list_of_speakers_ids": [2, 4],
                    "structure_level_list_of_speakers_ids": [3, 5],
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
                "list_of_speakers/4": {
                    "meeting_id": 1,
                    "structure_level_list_of_speakers_ids": [5],
                },
                "structure_level_list_of_speakers/5": {
                    "structure_level_id": 1,
                    "list_of_speakers_id": 4,
                    "meeting_id": 1,
                    "initial_time": 600,
                    "remaining_time": 600,
                },
            }
        )

    def test_set_start_time(self) -> None:
        now = round(time())
        response = self.request(
            "structure_level_list_of_speakers.update",
            {"id": 3, "current_start_time": now},
            internal=True,
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
            internal=True,
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

    def test_set_initial_time(self) -> None:
        response = self.request(
            "structure_level_list_of_speakers.update",
            {"id": 5, "initial_time": 100},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/5",
            {"initial_time": 100, "remaining_time": 100},
        )

    def test_set_initial_time_with_reduced_remaining_time(self) -> None:
        response = self.request(
            "structure_level_list_of_speakers.update",
            {"id": 3, "initial_time": 100},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/3",
            {"initial_time": 100, "remaining_time": 100},
        )

    def test_set_initial_time_with_speakers(self) -> None:
        self.set_models(
            {
                "speaker/1": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 2,
                    "structure_level_list_of_speakers_id": 3,
                    "begin_time": round(time()),
                }
            }
        )
        response = self.request(
            "structure_level_list_of_speakers.update",
            {"id": 3, "initial_time": 100},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/3",
            {"initial_time": 100, "remaining_time": 100},
        )

    def test_set_initial_time_with_other_field(self) -> None:
        for field in ("current_start_time", "spoken_time"):
            response = self.request(
                "structure_level_list_of_speakers.update",
                {"id": 3, "initial_time": 100, field: 100},
                internal=True,
            )
            self.assert_status_code(response, 400)
            self.assertIn(
                "Cannot set initial_time and " + field + " at the same time.",
                response.json["message"],
            )

    def test_set_internal_fields_externally(self) -> None:
        for field in ("current_start_time", "spoken_time"):
            response = self.request(
                "structure_level_list_of_speakers.update",
                {"id": 3, field: 100},
            )
            self.assert_status_code(response, 400)
            self.assertIn(
                field + " is not allowed to be set.",
                response.json["message"],
            )
