import fastjsonschema  # type: ignore

from ...models.topic import Topic
from ...shared.permissions.topic import TOPIC_CAN_MANAGE
from ...shared.schema import schema_version
from ..actions import register_action
from ..generics import UpdateAction

update_topic_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Update topics schema",
        "description": "An array of topics to be updated.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": Topic().get_schema("id"),
                "title": Topic().get_schema("title"),
                "text": Topic().get_schema("text"),
                "mediafile_attachment_ids": Topic().get_schema(
                    "mediafile_attachment_ids"
                ),
            },
            "required": ["id"],
            "additionalProperties": False,
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


@register_action("topic.update")
class TopicUpdate(UpdateAction):
    """
    Action to update simple topics that can be shown in the agenda.
    """

    model = Topic()
    schema = update_topic_schema
    manage_permission = TOPIC_CAN_MANAGE
