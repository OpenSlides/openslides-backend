from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class TopicDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "topic/111": {
                "title": "title_srtgb123",
                "meeting_id": 1,
            },
            "list_of_speakers/23": {
                "content_object_id": "topic/111",
                "meeting_id": 1,
            },
            "agenda_item/8": {"meeting_id": 1, "content_object_id": "topic/111"},
        }

    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "topic/111": {
                    "title": "title_srtgb123",
                    "meeting_id": 1,
                },
                "list_of_speakers/23": {
                    "content_object_id": "topic/111",
                    "meeting_id": 1,
                },
                "agenda_item/8": {"meeting_id": 1, "content_object_id": "topic/111"},
            }
        )
        response = self.request("topic.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("topic/111")

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "topic/112": {
                    "meeting_id": 1,
                    "title": "title_srtgb123",
                },
                "list_of_speakers/23": {
                    "content_object_id": "topic/112",
                    "meeting_id": 1,
                },
                "agenda_item/9": {"meeting_id": 1, "content_object_id": "topic/112"},
            }
        )
        response = self.request("topic.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("topic/112")

    def test_delete_correct_cascading(self) -> None:
        self.set_models(
            {
                "topic/111": {
                    "title": "title_srtgb123",
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
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("topic.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("topic/111")
        self.assert_model_not_exists("agenda_item/333")
        self.assert_model_not_exists("list_of_speakers/222")
        self.assert_model_not_exists("projection/1")
        self.assert_model_exists("projector/1", {"current_projection_ids": None})

    def test_create_delete(self) -> None:
        response = self.request("topic.create", {"meeting_id": 1, "title": "test"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("topic/1")
        self.assert_model_exists("list_of_speakers/1")
        response = self.request("topic.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("topic/1")
        self.assert_model_not_exists("list_of_speakers/1")

    def test_delete_with_agenda_item_and_filled_los(self) -> None:
        self.set_user_groups(1, [1])
        self.create_user_for_meeting(1)
        self.set_models(
            {
                "topic/1": {
                    "title": "tipuc",
                    "agenda_item_id": 3,
                    "list_of_speakers_id": 3,
                    "meeting_id": 1,
                },
                "agenda_item/3": {"content_object_id": "topic/1", "meeting_id": 1},
                "list_of_speakers/3": {
                    "content_object_id": "topic/1",
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
            }
        )
        response = self.request("topic.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("topic/1")
        self.assert_model_not_exists("agenda_item/3")
        self.assert_model_not_exists("list_of_speakers/3")
        self.assert_model_not_exists("speaker/1")
        self.assert_model_not_exists("speaker/2")
        self.assert_model_exists("meeting_user/1", {"speaker_ids": None})
        self.assert_model_exists("meeting_user/2", {"speaker_ids": None})

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
