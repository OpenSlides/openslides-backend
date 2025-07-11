from openslides_backend.models.models import AgendaItem
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase


class TopicCreateSystemTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "topic/41": {},
            }
        )
        response = self.request("topic.create", {"meeting_id": 1, "title": "test"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("topic/42")
        topic = self.get_model("topic/42")
        self.assertEqual(topic.get("meeting_id"), 1)
        self.assertEqual(topic.get("agenda_item_id"), 1)
        self.assertEqual(topic.get("sequential_number"), 1)
        self.assert_model_exists("agenda_item/1")
        agenda_item = self.get_model("agenda_item/1")
        self.assertEqual(agenda_item.get("meeting_id"), 1)
        self.assertEqual(agenda_item.get("content_object_id"), "topic/42")
        self.assert_model_exists(
            "list_of_speakers/1", {"content_object_id": "topic/42"}
        )
        self.assert_model_exists(
            "list_of_speakers/1", {"content_object_id": "topic/42"}
        )
        self.assertTrue(response.json["success"])
        self.assertEqual(response.json["message"], "Actions handled successfully")
        self.assertEqual(
            response.json["results"], [[{"id": 42, "sequential_number": 1}]]
        )

    def test_create_multiple_requests(self) -> None:
        self.create_meeting()
        response = self.request_json(
            [
                {
                    "action": "topic.create",
                    "data": [
                        {"meeting_id": 1, "title": "test1"},
                        {"meeting_id": 1, "title": "test2"},
                    ],
                },
                {
                    "action": "topic.create",
                    "data": [
                        {"meeting_id": 1, "title": "test3"},
                        {"meeting_id": 1, "title": "test4"},
                    ],
                },
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Datastore service sends HTTP 400. The following locks were broken: 'agenda_item/weight'",
            response.json["message"],
        )
        self.assert_model_not_exists("topic/1")
        self.assert_model_not_exists("topic/2")
        self.assert_model_not_exists("topic/3")
        self.assert_model_not_exists("topic/4")

    def test_create_more_fields(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {
                    "meeting_mediafile_ids": [11, 14],
                    "group_ids": [2],
                    "admin_group_id": 2,
                },
                "group/2": {"meeting_id": 1, "admin_group_for_meeting_id": 1},
                "mediafile/1": {
                    "owner_id": "meeting/1",
                    "meeting_mediafile_ids": [11],
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "meeting_mediafile/11": {"mediafile_id": 1, "meeting_id": 1},
                "mediafile/2": {
                    "owner_id": "meeting/1",
                    "child_ids": [3],
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "mediafile/3": {
                    "parent_id": 2,
                    "owner_id": "meeting/1",
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "mediafile/4": {
                    "owner_id": "meeting/1",
                    "meeting_mediafile_ids": [14],
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "meeting_mediafile/14": {"mediafile_id": 4, "meeting_id": 1},
                "tag/37": {"meeting_id": 1},
            }
        )
        response = self.request(
            "topic.create",
            {
                "meeting_id": 1,
                "title": "test",
                "agenda_type": AgendaItem.INTERNAL_ITEM,
                "agenda_duration": 60,
                "agenda_tag_ids": [37],
                "attachment_mediafile_ids": [1, 3, 4],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "topic/1",
            {
                "meeting_id": 1,
                "agenda_item_id": 1,
                "agenda_type": None,
                "attachment_meeting_mediafile_ids": [11, 15, 14],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/15",
            {
                "meeting_id": 1,
                "mediafile_id": 3,
                "attachment_ids": ["topic/1"],
                "inherited_access_group_ids": [2],
                "access_group_ids": None,
                "is_public": False,
            },
        )
        self.assert_model_exists(
            "agenda_item/1",
            {
                "meeting_id": 1,
                "content_object_id": "topic/1",
                "type": AgendaItem.INTERNAL_ITEM,
                "duration": 60,
                "weight": 1,
                "tag_ids": [37],
            },
        )
        self.assert_model_exists(
            "tag/37", {"meeting_id": 1, "tagged_ids": ["agenda_item/1"]}
        )

    def test_create_multiple_in_one_request(self) -> None:
        self.create_meeting()
        response = self.request_multi(
            "topic.create",
            [
                {
                    "meeting_id": 1,
                    "title": "A",
                    "agenda_type": AgendaItem.AGENDA_ITEM,
                    "agenda_weight": 1000,
                },
                {
                    "meeting_id": 1,
                    "title": "B",
                    "agenda_type": AgendaItem.AGENDA_ITEM,
                    "agenda_weight": 1001,
                },
            ],
        )
        self.assert_status_code(response, 200)
        topic = self.get_model("topic/1")
        self.assertEqual(topic.get("agenda_item_id"), 1)
        self.assertEqual(topic.get("sequential_number"), 1)
        agenda_item = self.get_model("agenda_item/1")
        self.assertEqual(agenda_item.get("meeting_id"), 1)
        self.assertEqual(agenda_item.get("content_object_id"), "topic/1")
        self.assertEqual(agenda_item.get("type"), AgendaItem.AGENDA_ITEM)
        self.assertEqual(agenda_item.get("weight"), 1000)
        topic = self.get_model("topic/2")
        self.assertEqual(topic.get("agenda_item_id"), 2)
        self.assertEqual(topic.get("sequential_number"), 2)
        agenda_item = self.get_model("agenda_item/2")
        self.assertEqual(agenda_item.get("meeting_id"), 1)
        self.assertEqual(agenda_item.get("content_object_id"), "topic/2")
        self.assertEqual(agenda_item.get("type"), AgendaItem.AGENDA_ITEM)
        self.assertEqual(agenda_item.get("weight"), 1001)
        meeting = self.get_model("meeting/1")
        self.assertEqual(meeting.get("topic_ids"), [1, 2])
        self.assertEqual(meeting.get("agenda_item_ids"), [1, 2])
        self.assertEqual(meeting.get("list_of_speakers_ids"), [1, 2])

    def test_create_multiple_with_existing_sequential_number(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "topic/1": {"meeting_id": 1, "sequential_number": 42},
            }
        )
        response = self.request_multi(
            "topic.create",
            [
                {
                    "meeting_id": 1,
                    "title": "A",
                },
                {
                    "meeting_id": 1,
                    "title": "B",
                },
            ],
        )
        self.assert_status_code(response, 200)
        topic = self.get_model("topic/2")
        self.assertEqual(topic.get("sequential_number"), 43)
        topic = self.get_model("topic/3")
        self.assertEqual(topic.get("sequential_number"), 44)

    def test_create_meeting_id_agenda_tag_ids_mismatch(self) -> None:
        """Tag 8 is from meeting 8 and a topic for meeting 1 should be created.
        This should lead to an error."""
        self.create_meeting()
        self.create_meeting(8)
        self.set_models(
            {
                "meeting/8": {
                    "tag_ids": [8],
                },
                "tag/8": {"name": "tag8", "meeting_id": 8},
            }
        )
        response = self.request(
            "topic.create",
            {
                "meeting_id": 1,
                "title": "A",
                "agenda_type": AgendaItem.INTERNAL_ITEM,
                "agenda_duration": 60,
                "agenda_tag_ids": [8],
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "The following models do not belong to meeting 1: ['tag/8']"
            in response.json["message"]
        )

    def test_create_with_agenda_tag_ids(self) -> None:
        """Tag 1 is from meeting 1 and a topic for meeting 1 should be created."""
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {"tag_ids": [1]},
                "tag/1": {"name": "test tag", "meeting_id": 1},
            }
        )
        response = self.request(
            "topic.create",
            {
                "meeting_id": 1,
                "title": "A",
                "agenda_type": AgendaItem.INTERNAL_ITEM,
                "agenda_duration": 60,
                "agenda_tag_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "topic/1", {"meeting_id": 1, "title": "A", "agenda_item_id": 1}
        )
        self.assert_model_exists(
            "agenda_item/1",
            {
                "meeting_id": 1,
                "type": AgendaItem.INTERNAL_ITEM,
                "duration": 60,
                "tag_ids": [1],
            },
        )
        self.assert_model_exists(
            "tag/1",
            {"meeting_id": 1, "name": "test tag", "tagged_ids": ["agenda_item/1"]},
        )

    def test_create_no_permission(self) -> None:
        self.base_permission_test(
            {}, "topic.create", {"meeting_id": 1, "title": "test"}
        )

    def test_create_permission(self) -> None:
        self.base_permission_test(
            {},
            "topic.create",
            {"meeting_id": 1, "title": "test"},
            Permissions.AgendaItem.CAN_MANAGE,
        )

    def test_create_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "topic.create",
            {"meeting_id": 1, "title": "test"},
        )
