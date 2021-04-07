from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase

DEFAULT_PASSWORD = "password"


class SpeakerDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model: Dict[str, Dict[str, Any]] = {
            "meeting/1": {"speaker_ids": [890]},
            "user/7": {
                "username": "test_username1",
                "speaker_$1_ids": [890],
                "speaker_$_ids": ["1"],
                "is_active": True,
                "default_password": DEFAULT_PASSWORD,
                "password": self.auth.hash(DEFAULT_PASSWORD),
            },
            "list_of_speakers/23": {"speaker_ids": [890], "meeting_id": 1},
            "speaker/890": {
                "user_id": 7,
                "list_of_speakers_id": 23,
                "meeting_id": 1,
            },
        }

    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/111": {"speaker_ids": [890]},
                "user/7": {
                    "username": "test_username1",
                    "speaker_$111_ids": [890],
                    "speaker_$_ids": ["111"],
                },
                "list_of_speakers/23": {"speaker_ids": [890]},
                "speaker/890": {
                    "user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 111,
                },
            }
        )
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/890")
        user = self.get_model("user/7")
        assert user.get("speaker_$111_ids") == []
        assert user.get("speaker_$_ids") == []

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/111": {"speaker_ids": [890]},
                "user/7": {
                    "username": "test_username1",
                    "speaker_$111_ids": [890],
                    "speaker_$_ids": ["111"],
                },
                "list_of_speakers/23": {"speaker_ids": [890]},
                "speaker/890": {
                    "user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 111,
                },
            }
        )
        response = self.request("speaker.delete", {"id": 889})
        self.assert_status_code(response, 400)
        self.assert_model_exists("speaker/890")

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model, "speaker.delete", {"id": 890}
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "speaker.delete",
            {"id": 890},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )

    def test_delete_self(self) -> None:
        self.create_meeting()
        self.user_id = 7
        self.set_models(self.permission_test_model)
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)
