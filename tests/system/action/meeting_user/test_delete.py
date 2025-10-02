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
        """Also checks that the user is successfully removed from a meeting he was present in."""
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "present_user_ids": [1],
                },
                "meeting/101": {
                    "is_active_in_organization_id": 1,
                    "present_user_ids": [1],
                },
                "user/1": {
                    "is_present_in_meeting_ids": [10, 101],
                    "meeting_user_ids": [5],
                },
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
        self.assert_model_exists(
            "user/1", {"is_present_in_meeting_ids": [101], "meeting_user_ids": []}
        )
        self.assert_model_exists("meeting/10", {"present_user_ids": []})
        self.assert_model_exists("meeting/101", {"present_user_ids": [1]})

    def test_delete_with_editor_and_working_group_speaker(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5],
                    "motion_editor_ids": [1],
                    "motion_working_group_speaker_ids": [2],
                    "motion_submitter_ids": [3],
                },
                "user/1": {
                    "meeting_user_ids": [5],
                },
                "meeting_user/5": {
                    "user_id": 1,
                    "motion_editor_ids": [1],
                    "motion_working_group_speaker_ids": [2],
                    "motion_submitter_ids": [3],
                    "meeting_id": 10,
                },
                "motion_editor/1": {
                    "meeting_user_id": 5,
                    "meeting_id": 10,
                },
                "motion_working_group_speaker/2": {
                    "meeting_user_id": 5,
                    "meeting_id": 10,
                },
                "motion_submitter/3": {
                    "meeting_user_id": 5,
                    "meeting_id": 10,
                },
            }
        )
        response = self.request("meeting_user.delete", {"id": 5})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("meeting_user/5")
        self.assert_model_exists("motion_editor/1", {"meeting_user_id": None})
        self.assert_model_exists(
            "motion_working_group_speaker/2", {"meeting_user_id": None}
        )
        self.assert_model_exists("motion_submitter/3", {"meeting_user_id": None})
        self.assert_model_exists(
            "meeting/10",
            {
                "motion_editor_ids": [1],
                "motion_working_group_speaker_ids": [2],
                "motion_submitter_ids": [3],
            },
        )

    def test_delete_with_chat_message(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "chat_message_ids": [1, 2],
                    "chat_group_ids": [1],
                },
                "meeting_user/5": {
                    "user_id": 1,
                    "meeting_id": 10,
                    "chat_message_ids": [1, 2],
                },
                "chat_group/1": {
                    "name": "cg1",
                    "meeting_id": 10,
                    "chat_message_ids": [1, 2],
                },
                "chat_message/1": {
                    "content": "message",
                    "created": 1234567890,
                    "meeting_user_id": 5,
                    "chat_group_id": 1,
                    "meeting_id": 10,
                },
                "chat_message/2": {
                    "content": "message",
                    "created": 1234567891,
                    "meeting_user_id": 5,
                    "chat_group_id": 1,
                    "meeting_id": 10,
                },
            }
        )
        response = self.request("meeting_user.delete", {"id": 5})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("meeting_user/5", {"chat_message_ids": [1, 2]})
        self.assert_model_exists("chat_message/1", {"meeting_user_id": None})
        self.assert_model_exists("chat_message/2", {"meeting_user_id": None})
