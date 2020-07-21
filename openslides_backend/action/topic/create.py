from ...models.topic import Topic
from ..action import register_action
from ..default_schema import DefaultSchema
from ..generics import CreateAction


@register_action("topic.create")
class TopicCreate(CreateAction):
    """
    Action to create simple topics that can be shown in the agenda.
    """

    model = Topic()
    schema = DefaultSchema(Topic()).get_create_schema(
        properties=["meeting_id", "title", "text", "attachment_ids"],
        required_properties=["meeting_id", "title"],
    )

    # TODO: Automaticly add agenda item.
