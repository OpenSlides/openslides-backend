from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class StructureLevelListOfSpeakersAddTimeTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.models: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "list_of_speakers_default_structure_level_time": 1000,
            },
            "topic/32": {
                "title": "leet improvement discussion",
                "sequential_number": 32,
                "meeting_id": 1,
            },
            "topic/42": {
                "title": "leet improvement discussion 2nd",
                "sequential_number": 42,
                "meeting_id": 1,
            },
            "agenda_item/1": {"content_object_id": "topic/32", "meeting_id": 1},
            "agenda_item/2": {"content_object_id": "topic/42", "meeting_id": 1},
            "list_of_speakers/1": {
                "meeting_id": 1,
                "sequential_number": 1,
                "content_object_id": "topic/32",
                "structure_level_list_of_speakers_ids": [1, 2, 3],
            },
            "list_of_speakers/2": {
                "meeting_id": 1,
                "sequential_number": 2,
                "content_object_id": "topic/42",
                "structure_level_list_of_speakers_ids": [4],
            },
            "structure_level/1": {
                "meeting_id": 1,
                "name": "monkey",
                "structure_level_list_of_speakers_ids": [1, 4],
            },
            "structure_level/2": {
                "meeting_id": 1,
                "name": "d.",
                "structure_level_list_of_speakers_ids": [2],
            },
            "structure_level/3": {
                "meeting_id": 1,
                "name": "ruffy",
                "structure_level_list_of_speakers_ids": [3],
            },
            "structure_level/4": {"meeting_id": 1, "name": "portgas"},
            "structure_level_list_of_speakers/1": {
                "meeting_id": 1,
                "structure_level_id": 1,
                "list_of_speakers_id": 1,
                "initial_time": 666,
                "remaining_time": -100,
            },
            "structure_level_list_of_speakers/2": {
                "meeting_id": 1,
                "structure_level_id": 2,
                "list_of_speakers_id": 1,
                "initial_time": 1000,
                "remaining_time": 200,
                "current_start_time": datetime.now(ZoneInfo("UTC")),
            },
            "structure_level_list_of_speakers/3": {
                "meeting_id": 1,
                "structure_level_id": 3,
                "list_of_speakers_id": 1,
                "initial_time": 1000,
                "additional_time": 200,
                "remaining_time": 400,
            },
            "structure_level_list_of_speakers/4": {
                "meeting_id": 1,
                "structure_level_id": 1,
                "list_of_speakers_id": 2,
                "initial_time": 1000,
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

    def test_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.models,
            "structure_level_list_of_speakers.add_time",
            {"id": 1},
        )
