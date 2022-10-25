from tests.system.action.base import BaseActionTestCase


class UserMeetingCreate(BaseActionTestCase):
    def test_create(self) -> None:
        self.set_models(
            {
                "meeting/10": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request("user_meeting.create", {"user_id": 1, "meeting_id": 10})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user_meeting/1", {"user_id": 1, "meeting_id": 10})
