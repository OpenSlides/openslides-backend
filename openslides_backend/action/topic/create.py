from typing import Iterable

from ...models.agenda_item import AgendaItem
from ...models.topic import Topic
from ...shared.interfaces import WriteRequestElement
from ...shared.patterns import FullQualifiedId
from ..action import register_action
from ..action_interface import ActionPayload
from ..agenda_item.create import AgendaItemCreate
from ..base import DataSet
from ..default_schema import DefaultSchema
from ..generics import CreateAction

schema = DefaultSchema(Topic()).get_create_schema(
    properties=["meeting_id", "title", "text", "attachment_ids"],
    required_properties=["meeting_id", "title"],
)

AGENDA_PREFIX = "agenda_"

agenda_creation_properties = {
    f"{AGENDA_PREFIX}type": {
        "description": "The type of the agenda item (common, internal, hidden).",
        "type": "integer",
        "enum": [
            AgendaItem.AGENDA_ITEM,
            AgendaItem.INTERNAL_ITEM,
            AgendaItem.HIDDEN_ITEM,
        ],
    },
    f"{AGENDA_PREFIX}parent_id": {
        "description": "The id of the parent agenda item.",
        "type": ["integer", "null"],
        "minimum": 1,
    },
    f"{AGENDA_PREFIX}comment": {
        "description": "The comment of the agenda item.",
        "type": "string",
    },
    f"{AGENDA_PREFIX}duration": {
        "description": "The duration of this agenda item object in seconds.",
        "type": "integer",
        "minimum": 0,
    },
    f"{AGENDA_PREFIX}weight": {
        "description": "The weight of the agenda item. Submitting null defaults to 0.",
        "type": "integer",
    },
}

schema["items"]["properties"].update(agenda_creation_properties)


@register_action("topic.create")
class TopicCreate(CreateAction):
    """
    Action to create simple topics that can be shown in the agenda.
    """

    model = Topic()
    schema = schema

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[WriteRequestElement]:
        agenda_item_creation = []
        for topic_element in dataset["data"]:
            additional_relation_models = {
                FullQualifiedId(
                    Topic.collection, topic_element["new_id"]
                ): topic_element["instance"]
            }
            action = AgendaItemCreate(
                "agenda_item.create",
                self.permission,
                self.database,
                additional_relation_models,
            )
            agenda_item_payload_element = {
                "meeting_id": topic_element["instance"]["meeting_id"],
                "content_object_id": f"topic/{topic_element['new_id']}",
            }
            for extra_field in agenda_creation_properties.keys():
                prefix_len = len(AGENDA_PREFIX)
                extra_field_without_prefix = extra_field[prefix_len:]
                value = topic_element["instance"].pop(extra_field, None)
                if value is not None:
                    agenda_item_payload_element[extra_field_without_prefix] = value
            agenda_item_payload: ActionPayload = [agenda_item_payload_element]
            agenda_item_creation.append((action, agenda_item_payload))

        yield from super().create_write_request_elements(dataset)

        for action, agenda_item_payload in agenda_item_creation:
            yield from action.perform(agenda_item_payload, self.user_id)
