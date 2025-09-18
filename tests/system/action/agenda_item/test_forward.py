from openslides_backend.services.datastore.with_database_context import (
    with_database_context,
)
from tests.system.action.base import BaseActionTestCase


class AgendaItemForwardActionTest(BaseActionTestCase):
    @with_database_context
    def create_topic_agenda_item(
        self,
        agenda_item_id: int = 1,
        topic_id: int = 10,
        meeting_id: int = 1,
        parent_id: int | None = None,
    ) -> None:
        """
        Creates an agenda_item linked to a topic.
        The list_of_speakers for the topic will have the id topic_id * 10.
        """
        meeting = self.datastore.get(
            f"meeting/{meeting_id}",
            ["agenda_item_ids", "topic_ids", "list_of_speakers_ids"],
            lock_result=False,
        )
        self.set_models(
            {
                f"meeting/{meeting_id}": {
                    "agenda_item_ids": [
                        *meeting.get("agenda_item_ids", []),
                        agenda_item_id,
                    ],
                    "topic_ids": [*meeting.get("topic_ids", []), topic_id],
                    "list_of_speakers_ids": [
                        *meeting.get("list_of_speakers_ids", []),
                        topic_id * 10,
                    ],
                },
                f"agenda_item/{agenda_item_id}": {
                    "content_object_id": f"topic/{topic_id}",
                    "meeting_id": meeting_id,
                    "weight": agenda_item_id,
                },
                f"topic/{topic_id}": {
                    "agenda_item_id": agenda_item_id,
                    "list_of_speakers_id": topic_id * 10,
                    "meeting_id": meeting_id,
                    "title": f"Topic {topic_id}",
                    "sequential_number": topic_id,
                },
                f"list_of_speakers/{topic_id*10}": {
                    "content_object_id": f"topic/{topic_id}",
                    "meeting_id": meeting_id,
                    "sequential_number": topic_id * 10,
                },
            }
        )
        if parent_id:
            parent = self.datastore.get(
                f"agenda_item/{parent_id}", ["child_ids"], lock_result=False
            )
            self.set_models(
                {
                    f"agenda_item/{agenda_item_id}": {"parent_id": parent_id},
                    f"agenda_item/{parent_id}": {
                        "child_ids": [*parent.get("child_ids", []), agenda_item_id],
                    },
                }
            )

    def test_simple(self) -> None:
        self.create_meeting()
        self.create_meeting(4)
        self.create_meeting(7)
        self.set_models(
            {
                "committee/60": {"forward_agenda_to_committee_ids": [63, 66]},
                "committee/63": {"receive_agenda_forwardings_from_committee_ids": [60]},
                "committee/67": {"receive_agenda_forwardings_from_committee_ids": [60]},
            }
        )
        self.create_topic_agenda_item()
        self.create_topic_agenda_item(2, 20, parent_id=1)
        self.create_topic_agenda_item(3, 30, parent_id=1)
        self.create_topic_agenda_item(4, 40, parent_id=3)
        self.create_topic_agenda_item(5, 50)
        self.create_topic_agenda_item(6, 60, parent_id=5)
        self.create_topic_agenda_item(7, 70, parent_id=6)
        self.create_topic_agenda_item(8, 80, parent_id=7)
        self.create_topic_agenda_item(9, 90, parent_id=8)

        response = self.request(
            "agenda_item.forward",
            {
                "meeting_ids": [4, 7],
                "agenda_item_ids": [1, 2, 3, 4, 6, 9],
            },
        )
        self.assert_status_code(response, 200)
        # TODO: assertions

    def test_simple_with_flags(self) -> None:
        self.create_meeting()
        self.create_meeting(4)
        self.create_meeting(7)
        self.set_models(
            {
                "committee/60": {"forward_agenda_to_committee_ids": [63, 66]},
                "committee/63": {"receive_agenda_forwardings_from_committee_ids": [60]},
                "committee/67": {"receive_agenda_forwardings_from_committee_ids": [60]},
            }
        )
        self.create_topic_agenda_item()
        self.create_topic_agenda_item(2, 20, parent_id=1)
        self.create_topic_agenda_item(3, 30, parent_id=1)
        self.create_topic_agenda_item(4, 40, parent_id=3)
        self.create_topic_agenda_item(5, 50)
        self.create_topic_agenda_item(6, 60, parent_id=5)
        self.create_topic_agenda_item(7, 70, parent_id=6)
        self.create_topic_agenda_item(8, 80, parent_id=7)
        self.create_topic_agenda_item(9, 90, parent_id=8)

        response = self.request(
            "agenda_item.forward",
            {
                "meeting_ids": [4, 7],
                "agenda_item_ids": [1, 2, 3, 4, 6, 9],
                "with_speakers": True,
                "with_moderator_notes": True,
                "with_attachments": True,
            },
        )
        self.assert_status_code(response, 200)
        # TODO: assertions
