from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class StructureLevelListOfSpeakersCreateTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.models: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "list_of_speakers_default_structure_level_time": 600,
                "structure_level_ids": [1],
                "list_of_speakers_ids": [2],
            },
            "structure_level/1": {"meeting_id": 1},
            "list_of_speakers/2": {"meeting_id": 1},
        }
        self.set_models(self.models)

    def test_create_empty_data(self) -> None:
        response = self.request("structure_level_list_of_speakers.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['list_of_speakers_id', 'structure_level_id'] properties",
            response.json["message"],
        )

    def test_create_required_fields(self) -> None:
        response = self.request(
            "structure_level_list_of_speakers.create",
            {
                "structure_level_id": 1,
                "list_of_speakers_id": 2,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/1",
            {
                "structure_level_id": 1,
                "list_of_speakers_id": 2,
                "meeting_id": 1,
                "initial_time": 600,
                "remaining_time": 600,
            },
        )
        self.assert_model_exists(
            "meeting/1",
            {
                "structure_level_list_of_speakers_ids": [1],
            },
        )
        self.assert_model_exists(
            "structure_level/1",
            {
                "structure_level_list_of_speakers_ids": [1],
            },
        )
        self.assert_model_exists(
            "list_of_speakers/2",
            {
                "structure_level_list_of_speakers_ids": [1],
            },
        )

    def test_create_all_fields(self) -> None:
        response = self.request(
            "structure_level_list_of_speakers.create",
            {
                "structure_level_id": 1,
                "list_of_speakers_id": 2,
                "initial_time": 300,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/1",
            {
                "structure_level_id": 1,
                "list_of_speakers_id": 2,
                "meeting_id": 1,
                "initial_time": 300,
                "remaining_time": 300,
            },
        )

    def test_create_duplicate(self) -> None:
        self.set_models(
            {
                "structure_level_list_of_speakers/3": {
                    "meeting_id": 1,
                    "structure_level_id": 1,
                    "list_of_speakers_id": 2,
                },
            }
        )
        response = self.request(
            "structure_level_list_of_speakers.create",
            {
                "structure_level_id": 1,
                "list_of_speakers_id": 2,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "(structure_level_id, list_of_speakers_id) must be unique.",
            response.json["message"],
        )
        self.assert_model_not_exists("structure_level_list_of_speakers/2")

    def test_create_structure_level_countdowns_deactivated(self) -> None:
        self.set_models(
            {"meeting/1": {"list_of_speakers_default_structure_level_time": 0}}
        )
        response = self.request(
            "structure_level_list_of_speakers.create",
            {
                "structure_level_id": 1,
                "list_of_speakers_id": 2,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Structure level countdowns are deactivated",
            response.json["message"],
        )

    def test_create_structure_level_countdowns_deactivated_2(self) -> None:
        self.set_models(
            {"meeting/1": {"list_of_speakers_default_structure_level_time": None}}
        )
        response = self.request(
            "structure_level_list_of_speakers.create",
            {
                "structure_level_id": 1,
                "list_of_speakers_id": 2,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Structure level countdowns are deactivated",
            response.json["message"],
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            self.models,
            "structure_level_list_of_speakers.create",
            {
                "structure_level_id": 1,
                "list_of_speakers_id": 2,
            },
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            self.models,
            "structure_level_list_of_speakers.create",
            {
                "structure_level_id": 1,
                "list_of_speakers_id": 2,
            },
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.models,
            "structure_level_list_of_speakers.create",
            {
                "structure_level_id": 1,
                "list_of_speakers_id": 2,
            },
        )
