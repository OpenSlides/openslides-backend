from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class TopicDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "topic/111": {"title": "title_srtgb123", "meeting_id": 1}
        }

    def test_delete_correct(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "topic/111": {"title": "title_srtgb123", "meeting_id": 1},
            }
        )
        response = self.request("topic.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("topic/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("topic/112", {"title": "title_srtgb123"})
        response = self.request("topic.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("topic/112")

    def test_delete_correct_cascading(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {
                    "all_projection_ids": [1],
                },
                "topic/111": {
                    "title": "title_srtgb123",
                    "list_of_speakers_id": 222,
                    "agenda_item_id": 333,
                    "projection_ids": [1],
                    "meeting_id": 1,
                },
                "list_of_speakers/222": {
                    "closed": False,
                    "content_object_id": "topic/111",
                    "meeting_id": 1,
                },
                "agenda_item/333": {
                    "comment": "test_comment_ewoirzewoirioewr",
                    "content_object_id": "topic/111",
                    "meeting_id": 1,
                },
                "projection/1": {
                    "content_object_id": "topic/111",
                    "current_projector_id": 1,
                    "meeting_id": 1,
                },
                "projector/1": {
                    "current_projection_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("topic.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("topic/111")
        self.assert_model_deleted("agenda_item/333")
        self.assert_model_deleted("list_of_speakers/222")
        self.assert_model_deleted("projection/1")
        self.assert_model_exists("projector/1", {"current_projection_ids": []})

    def test_create_delete(self) -> None:
        self.create_meeting()
        response = self.request("topic.create", {"meeting_id": 1, "title": "test"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("topic/1")
        self.assert_model_exists("list_of_speakers/1")
        response = self.request("topic.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("topic/1")
        self.assert_model_deleted("list_of_speakers/1")

    def test_delete_with_agenda_item_and_filled_los(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {
                    "agenda_item_ids": [3, 14],
                    "list_of_speakers_ids": [3],
                    "topic_ids": [1],
                    "speaker_ids": [1, 2],
                    "meeting_user_ids": [1, 2],
                },
                "topic/1": {
                    "agenda_item_id": 3,
                    "list_of_speakers_id": 3,
                    "meeting_id": 1,
                },
                "agenda_item/3": {"content_object_id": "topic/1", "meeting_id": 1},
                "list_of_speakers/3": {
                    "content_object_id": "topic/1",
                    "speaker_ids": [1, 2],
                    "meeting_id": 1,
                },
                "speaker/1": {
                    "list_of_speakers_id": 3,
                    "meeting_user_id": 1,
                    "meeting_id": 1,
                },
                "speaker/2": {
                    "list_of_speakers_id": 3,
                    "meeting_user_id": 2,
                    "meeting_id": 1,
                },
                "user/1": {"meeting_user_ids": [1]},
                "user/2": {"meeting_user_ids": [2]},
                "meeting_user/1": {"user_id": 1, "meeting_id": 1, "speaker_ids": [1]},
                "meeting_user/2": {"user_id": 2, "meeting_id": 1, "speaker_ids": [2]},
            }
        )
        response = self.request("topic.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("topic/1")
        self.assert_model_deleted("agenda_item/3")
        self.assert_model_deleted("list_of_speakers/3")
        self.assert_model_deleted("speaker/1")
        self.assert_model_deleted("speaker/2")
        self.assert_model_exists("meeting_user/1", {"speaker_ids": []})
        self.assert_model_exists("meeting_user/2", {"speaker_ids": []})

    def test_delete_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models, "topic.delete", {"id": 111}
        )

    def test_delete_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "topic.delete",
            {"id": 111},
            Permissions.AgendaItem.CAN_MANAGE,
        )

    def test_delete_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "topic.delete",
            {"id": 111},
        )
