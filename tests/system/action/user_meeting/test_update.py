from tests.system.action.base import BaseActionTestCase


class UserMeetingUpdate(BaseActionTestCase):
    def test_update(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "user_meeting_ids": [5],
                },
                "meeting/11": {"is_active_in_organization_id": 1},
                "user_meeting/5": {"user_id": 1, "meeting_id": 10},
            }
        )
        response = self.request("user_meeting.update", {"id": 5, "meeting_id": 11})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user_meeting/5", {"meeting_id": 11})
