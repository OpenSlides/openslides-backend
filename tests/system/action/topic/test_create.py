from openslides_backend.models.models import AgendaItem
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase


class TopicCreateSystemTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_meeting()
        self.create_topic(41, 1, {"sequential_number": 1})
        response = self.request("topic.create", {"meeting_id": 1, "title": "test"})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "topic/42",
            {
                "meeting_id": 1,
                "agenda_item_id": 42,
                "sequential_number": 2,
                "list_of_speakers_id": 42,
            },
        )
        self.assert_model_exists(
            "agenda_item/42", {"meeting_id": 1, "content_object_id": "topic/42"}
        )
        self.assert_model_exists(
            "list_of_speakers/42", {"content_object_id": "topic/42"}
        )
        self.assertTrue(response.json["success"])
        self.assertEqual(response.json["message"], "Actions handled successfully")
        self.assertEqual(
            response.json["results"], [[{"id": 42, "sequential_number": 2}]]
        )

    def test_create_multiple_requests(self) -> None:
        self.create_meeting()
        response = self.request_json(
            [
                {
                    "action": "topic.create",
                    "data": [
                        {
                            "meeting_id": 1,
                            "agenda_type": AgendaItem.AGENDA_ITEM,
                            "title": "test1",
                        },
                        {
                            "meeting_id": 1,
                            "agenda_type": AgendaItem.AGENDA_ITEM,
                            "title": "test2",
                        },
                    ],
                },
                {
                    "action": "topic.create",
                    "data": [
                        {
                            "meeting_id": 1,
                            "agenda_type": AgendaItem.AGENDA_ITEM,
                            "title": "test3",
                        },
                        {
                            "meeting_id": 1,
                            "agenda_type": AgendaItem.AGENDA_ITEM,
                            "title": "test4",
                        },
                    ],
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("topic/1", {"meeting_id": 1, "title": "test1"})
        self.assert_model_exists("topic/2", {"meeting_id": 1, "title": "test2"})
        self.assert_model_exists("topic/3", {"meeting_id": 1, "title": "test3"})
        self.assert_model_exists("topic/4", {"meeting_id": 1, "title": "test4"})
        self.assert_model_exists(
            "agenda_item/1",
            {
                "content_object_id": "topic/1",
                "type": AgendaItem.AGENDA_ITEM,
                "weight": 1,
            },
        )
        self.assert_model_exists(
            "agenda_item/2",
            {
                "content_object_id": "topic/2",
                "type": AgendaItem.AGENDA_ITEM,
                "weight": 2,
            },
        )
        self.assert_model_exists(
            "agenda_item/3",
            {
                "content_object_id": "topic/3",
                "type": AgendaItem.AGENDA_ITEM,
                "weight": 3,
            },
        )
        self.assert_model_exists(
            "agenda_item/4",
            {
                "content_object_id": "topic/4",
                "type": AgendaItem.AGENDA_ITEM,
                "weight": 4,
            },
        )

    def test_create_more_fields(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "mediafile/1": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "meeting_mediafile/11": {
                    "is_public": False,
                    "mediafile_id": 1,
                    "meeting_id": 1,
                },
                "mediafile/2": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "mediafile/3": {
                    "parent_id": 2,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "mediafile/4": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "meeting_mediafile/14": {
                    "is_public": False,
                    "mediafile_id": 4,
                    "meeting_id": 1,
                },
                "tag/37": {"name": "night", "meeting_id": 1},
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
                "attachment_meeting_mediafile_ids": [11, 14, 15],
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
        self.assert_model_not_exists("meeting_mediafile/16")
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

    def test_create_multiple_with_existing_sequential_number(self) -> None:
        self.create_meeting()
        self.create_topic(1, 1, {"sequential_number": 42})
        response = self.request_multi(
            "topic.create",
            [
                {"meeting_id": 1, "title": "A"},
                {"meeting_id": 1, "title": "B"},
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("topic/2", {"sequential_number": 43})
        self.assert_model_exists("topic/3", {"sequential_number": 44})

    def test_create_meeting_id_agenda_tag_ids_mismatch(self) -> None:
        """Tag 8 is from meeting 8 and a topic for meeting 1 should be created.
        This should lead to an error."""
        self.create_meeting()
        self.create_meeting(8)
        self.set_models({"tag/8": {"name": "tag8", "meeting_id": 8}})
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
        self.set_models({"tag/1": {"name": "test tag", "meeting_id": 1}})
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
