from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class SpeakerSortActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "list_of_speakers/222": {"meeting_id": 1},
            "speaker/31": {"list_of_speakers_id": 222, "meeting_id": 1},
            "speaker/32": {"list_of_speakers_id": 222, "meeting_id": 1},
        }

    def test_sort_correct_1(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "list_of_speakers/222": {"meeting_id": 1},
                "speaker/31": {"list_of_speakers_id": 222, "meeting_id": 1},
                "speaker/32": {"list_of_speakers_id": 222, "meeting_id": 1},
            }
        )
        response = self.request(
            "speaker.sort", {"list_of_speakers_id": 222, "speaker_ids": [32, 31]}
        )
        self.assert_status_code(response, 200)
        model_31 = self.get_model("speaker/31")
        assert model_31.get("weight") == 2
        model_32 = self.get_model("speaker/32")
        assert model_32.get("weight") == 1

    def test_sort_missing_model(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "list_of_speakers/222": {"meeting_id": 1},
                "speaker/31": {"list_of_speakers_id": 222, "meeting_id": 1},
            }
        )
        response = self.request(
            "speaker.sort", {"list_of_speakers_id": 222, "speaker_ids": [32, 31]}
        )
        self.assert_status_code(response, 400)
        assert (
            "speaker sorting failed, because element speaker/32 doesn't exist."
            in response.json["message"]
        )

    def test_sort_another_section_db(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "list_of_speakers/222": {"meeting_id": 1},
                "speaker/31": {"list_of_speakers_id": 222, "meeting_id": 1},
                "speaker/32": {"list_of_speakers_id": 222, "meeting_id": 1},
                "speaker/33": {"list_of_speakers_id": 222, "meeting_id": 1},
            }
        )
        response = self.request(
            "speaker.sort", {"list_of_speakers_id": 222, "speaker_ids": [32, 31]}
        )
        self.assert_status_code(response, 400)
        assert (
            "speaker sorting failed, because some elements were not included in the call."
            in response.json["message"]
        )

    def test_sort_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "speaker.sort",
            {"list_of_speakers_id": 222, "speaker_ids": [32, 31]},
        )

    def test_sort_permisions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "speaker.sort",
            {"list_of_speakers_id": 222, "speaker_ids": [32, 31]},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )
