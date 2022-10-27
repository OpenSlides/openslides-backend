from tests.system.action.base import BaseActionTestCase


class MeetingUserUpdate(BaseActionTestCase):
    def test_update(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5],
                },
                "meeting/11": {"is_active_in_organization_id": 1},
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
            }
        )
        response = self.request("meeting_user.update", {"id": 5, "meeting_id": 11})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/5", {"meeting_id": 11})
