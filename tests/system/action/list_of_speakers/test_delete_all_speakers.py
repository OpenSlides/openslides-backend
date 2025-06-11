from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ListOfSpeakersDeleteAllSpeakersActionTester(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {"speaker_ids": [1], "is_active_in_organization_id": 1},
            "list_of_speakers/111": {
                "closed": False,
                "meeting_id": 1,
                "speaker_ids": [1],
            },
            "speaker/1": {"list_of_speakers_id": 111, "meeting_id": 1},
        }

    def test_delete_all_correct(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "meeting/222": {
                    "speaker_ids": list(range(1, 11)),
                },
                "list_of_speakers/111": {
                    "closed": False,
                    "meeting_id": 222,
                    "speaker_ids": list(range(1, 11)),
                },
            }
        )
        for i in range(1, 11):
            self.create_model(
                f"speaker/{i}", {"list_of_speakers_id": 111, "meeting_id": 222}
            )
        response = self.request("list_of_speakers.delete_all_speakers", {"id": 111})
        self.assert_status_code(response, 200)

        for i in range(1, 11):
            self.assert_model_not_exists(f"speaker/{i}")

    def test_wrong_id(self) -> None:
        response = self.request("list_of_speakers.delete_all_speakers", {"id": 111})
        self.assert_status_code(response, 400)
        assert (
            "Model 'list_of_speakers/111' does not exist." in response.json["message"]
        )

    def test_delete_all_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "list_of_speakers.delete_all_speakers",
            {"id": 111},
        )

    def test_delete_all_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "list_of_speakers.delete_all_speakers",
            {"id": 111},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )

    def test_delete_all_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "list_of_speakers.delete_all_speakers",
            {"id": 111},
        )
