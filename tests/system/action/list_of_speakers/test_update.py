from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ListOfSpeakersUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "list_of_speakers/111": {"closed": False, "meeting_id": 1},
        }

    def test_update_correct(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "list_of_speakers/111": {"closed": False, "meeting_id": 222},
            }
        )
        response = self.request("list_of_speakers.update", {"id": 111, "closed": True})
        self.assert_status_code(response, 200)

        model = self.get_model("list_of_speakers/111")
        assert model.get("closed") is True

    def test_update_wrong_id(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "list_of_speakers/111": {"closed": False, "meeting_id": 222},
            }
        )

        response = self.request("list_of_speakers.update", {"id": 112, "closed": True})
        self.assert_status_code(response, 400)
        model = self.get_model("list_of_speakers/111")
        assert model.get("closed") is False

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "list_of_speakers.update",
            {"id": 111, "closed": True},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "list_of_speakers.update",
            {"id": 111, "closed": True},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "list_of_speakers.update",
            {"id": 111, "closed": True},
        )

    def test_update_moderator_notes_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "list_of_speakers.update",
            {"id": 111, "moderator_notes": "test"},
            Permissions.ListOfSpeakers.CAN_MANAGE,
            fail=True,
        )

    def test_update_moderator_notes_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "list_of_speakers.update",
            {"id": 111, "moderator_notes": "test"},
            Permissions.ListOfSpeakers.CAN_MANAGE_MODERATOR_NOTES,
        )
