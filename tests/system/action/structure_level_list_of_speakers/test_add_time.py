from time import time
from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class StructureLevelListOfSpeakersAddTimeTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.models: Dict[str, Dict[str, Any]] = {
            "meeting/1": {
                "is_active_in_organization_id": 1,
                "list_of_speakers_default_structure_level_time": 1000,
                "structure_level_ids": [1, 2, 3, 4],
                "list_of_speakers_ids": [1, 2],
                "structure_level_list_of_speakers_ids": [1, 2, 3, 4],
            },
            "list_of_speakers/1": {
                "meeting_id": 1,
                "structure_level_list_of_speakers_ids": [1, 2, 3],
            },
            "list_of_speakers/2": {
                "meeting_id": 1,
                "structure_level_list_of_speakers_ids": [4],
            },
            "structure_level/1": {
                "meeting_id": 1,
                "structure_level_list_of_speakers_ids": [1, 4],
            },
            "structure_level/2": {
                "meeting_id": 1,
                "structure_level_list_of_speakers_ids": [2],
            },
            "structure_level/3": {
                "meeting_id": 1,
                "structure_level_list_of_speakers_ids": [3],
            },
            "structure_level/4": {"meeting_id": 1},
            "structure_level_list_of_speakers/1": {
                "meeting_id": 1,
                "structure_level_id": 1,
                "list_of_speakers_id": 1,
                "remaining_time": -100,
            },
            "structure_level_list_of_speakers/2": {
                "meeting_id": 1,
                "structure_level_id": 2,
                "list_of_speakers_id": 1,
                "remaining_time": 200,
                "current_start_time": int(time()),
            },
            "structure_level_list_of_speakers/3": {
                "meeting_id": 1,
                "structure_level_id": 3,
                "list_of_speakers_id": 1,
                "additional_time": 200,
                "remaining_time": 400,
            },
            "structure_level_list_of_speakers/4": {
                "meeting_id": 1,
                "structure_level_id": 1,
                "list_of_speakers_id": 2,
                "remaining_time": 300,
            },
        }
        self.set_models(self.models)

    def test_empty_data(self) -> None:
        response = self.request("structure_level_list_of_speakers.add_time", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['id'] properties",
            response.json["message"],
        )

    def test_add_time(self) -> None:
        response = self.request(
            "structure_level_list_of_speakers.add_time",
            {"id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/1",
            {
                "remaining_time": 0,
                "additional_time": 100,
            },
        )
        self.assert_model_exists(
            "structure_level_list_of_speakers/2",
            {
                "remaining_time": 300,
                "additional_time": 100,
            },
        )
        self.assert_model_exists(
            "structure_level_list_of_speakers/3",
            {
                "remaining_time": 500,
                "additional_time": 300,
            },
        )
        self.assert_model_exists(
            "structure_level_list_of_speakers/4",
            {
                "remaining_time": 300,
                "additional_time": None,
            },
        )
        self.assert_model_not_exists("structure_level_list_of_speakers/5")

    def test_current_speaker(self) -> None:
        response = self.request(
            "structure_level_list_of_speakers.add_time",
            {"id": 2},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Stop the current speaker before adding time",
            response.json["message"],
        )

    def test_positive_remaining_time(self) -> None:
        response = self.request(
            "structure_level_list_of_speakers.add_time",
            {"id": 3},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "You can only add time if the remaining time is negative",
            response.json["message"],
        )

    def test_countdowns_deactivated(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_default_structure_level_time": 0,
                }
            }
        )
        response = self.request(
            "structure_level_list_of_speakers.add_time",
            {"id": 1},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Structure level countdowns are deactivated",
            response.json["message"],
        )

    def test_no_permissions(self) -> None:
        self.base_permission_test(
            self.models,
            "structure_level_list_of_speakers.add_time",
            {"id": 1},
        )

    def test_permissions(self) -> None:
        self.base_permission_test(
            self.models,
            "structure_level_list_of_speakers.add_time",
            {"id": 1},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )
