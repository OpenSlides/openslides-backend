from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class TopicUpdateTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {"name": "test", "is_active_in_organization_id": 1},
            "topic/1": {"title": "test", "meeting_id": 1},
        }

    def test_update_simple(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "test", "is_active_in_organization_id": 1},
                "topic/1": {"title": "test", "meeting_id": 1},
            }
        )
        response = self.request(
            "topic.update", {"id": 1, "title": "test2", "text": "text"}
        )
        self.assert_status_code(response, 200)
        topic = self.get_model("topic/1")
        self.assertEqual(topic.get("title"), "test2")
        self.assertEqual(topic.get("text"), "text")

    def test_update_text_with_iframe(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "test", "is_active_in_organization_id": 1},
                "topic/1": {"title": "test", "meeting_id": 1},
            }
        )
        response = self.request(
            "topic.update", {"id": 1, "text": "<IFRAME>text</IFRAME>"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "topic/1",
            {
                "text": '<iframe sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer">text</iframe>'
            },
        )

    def test_update_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "topic.update",
            {"id": 1, "title": "test2", "text": "text"},
        )

    def test_update_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "topic.update",
            {"id": 1, "title": "test2", "text": "text"},
            Permissions.AgendaItem.CAN_MANAGE,
        )

    def test_update_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "topic.update",
            {"id": 1, "title": "test2", "text": "text"},
        )
