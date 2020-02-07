import fastjsonschema  # type: ignore

from ...models.topic import Topic
from ...shared.permissions.topic import TOPIC_CAN_MANAGE
from ...shared.schema import schema_version
from ..actions import register_action
from ..generics import CreateAction

create_topic_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "New topics schema",
        "description": "An array of new topics.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "meeting_id": Topic().get_schema("meeting_id"),
                "title": Topic().get_schema("title"),
                "text": Topic().get_schema("text"),
                "mediafile_attachment_ids": Topic().get_schema(
                    "mediafile_attachment_ids"
                ),
            },
            "required": ["meeting_id", "title"],
            "additionalProperties": False,
        },
        "minItems": 1,
        "uniqueItems": False,
    }
)


@register_action("topic.create")
class TopicCreate(CreateAction):
    """
    Action to create simple topics that can be shown in the agenda.
    """

    model = Topic()
    schema = create_topic_schema
    permissions = [TOPIC_CAN_MANAGE]
