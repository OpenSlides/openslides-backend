from tests.system.action.base import BaseActionTestCase


class MeetingUserCreate(BaseActionTestCase):
    def test_create(self) -> None:
        self.set_models(
            {
                "meeting/10": {"is_active_in_organization_id": 1},
            }
        )
        test_dict = {
            "user_id": 1,
            "meeting_id": 10,
            "comment": "test blablaba",
        }
        response = self.request("meeting_user.create", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/1", test_dict)
