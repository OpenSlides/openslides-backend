from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class TopicUpdateTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: Dict[str, Dict[str, Any]] = {
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

    def test_update_tag_ids_add(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "test", "is_active_in_organization_id": 1},
                "topic/1": {"title": "test", "meeting_id": 1},
                "tag/1": {"name": "tag", "meeting_id": 1},
            }
        )
        response = self.request("topic.update", {"id": 1, "tag_ids": [1]})
        self.assert_status_code(response, 200)
        topic = self.get_model("topic/1")
        self.assertEqual(topic.get("tag_ids"), [1])

    def test_update_tag_ids_remove(self) -> None:
        self.test_update_tag_ids_add()
        response = self.request("topic.update", {"id": 1, "tag_ids": []})
        self.assert_status_code(response, 200)
        topic = self.get_model("topic/1")
        self.assertEqual(topic.get("tag_ids"), [])

    def test_update_multiple_with_tag(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "test", "is_active_in_organization_id": 1},
                "tag/1": {
                    "name": "tag",
                    "meeting_id": 1,
                    "tagged_ids": ["topic/1", "topic/2"],
                },
                "topic/1": {"title": "test", "meeting_id": 1, "tag_ids": [1]},
                "topic/2": {"title": "test", "meeting_id": 1, "tag_ids": [1]},
            }
        )
        response = self.request_multi(
            "topic.update", [{"id": 1, "tag_ids": []}, {"id": 2, "tag_ids": []}]
        )
        self.assert_status_code(response, 200)
        topic = self.get_model("topic/1")
        self.assertEqual(topic.get("tag_ids"), [])
        topic = self.get_model("topic/2")
        self.assertEqual(topic.get("tag_ids"), [])
        tag = self.get_model("tag/1")
        self.assertEqual(tag.get("tagged_ids"), [])

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
