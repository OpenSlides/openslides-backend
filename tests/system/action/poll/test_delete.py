from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class PollDeleteTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "poll/111": {"meeting_id": 1},
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request("poll.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("poll/111")

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "poll/112": {"meeting_id": 1},
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request("poll.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("poll/112")

    def test_delete_correct_cascading(self) -> None:
        self.set_models(
            {
                "poll/111": {
                    "option_ids": [42],
                    "meeting_id": 1,
                },
                "option/42": {"poll_id": 111, "meeting_id": 1},
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request("poll.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("poll/111")
        self.assert_model_deleted("option/42")

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            {"poll/111": {"meeting_id": 1}}, "poll.delete", {"id": 111}
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {"poll/111": {"meeting_id": 1}},
            "poll.delete",
            {"id": 111},
            Permissions.Poll.CAN_MANAGE,
        )
