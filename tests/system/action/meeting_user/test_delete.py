from tests.system.action.base import BaseActionTestCase


class MeetingUserDelete(BaseActionTestCase):
    def test_delete(self) -> None:
        self.set_models(
            {
                "meeting/10": {"is_active_in_organization_id": 1},
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
            }
        )
        response = self.request("meeting_user.delete", {"id": 5})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("meeting_user/5")

    def test_delete_with_speaker(self) -> None:
        self.set_models(
            {
                "meeting/10": {"is_active_in_organization_id": 1},
                "meeting_user/5": {
                    "user_id": 1,
                    "meeting_id": 10,
                    "speaker_ids": [1, 2],
                },
                "speaker/1": {
                    "meeting_user_id": 5,
                    "meeting_id": 10,
                },
                "speaker/2": {
                    "meeting_user_id": 5,
                    "meeting_id": 10,
                    "begin_time": 123456,
                },
            }
        )
        response = self.request("meeting_user.delete", {"id": 5})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("meeting_user/5")
        self.assert_model_deleted("speaker/1")
        self.assert_model_exists("speaker/2", {"meeting_id": 10, "begin_time": 123456})
