from ...models.topic import Topic
from ..action import register_action
from ..default_schema import DefaultSchema
from ..generics import UpdateAction


@register_action("topic.update")
class TopicUpdate(UpdateAction):
    """
    Action to update simple topics that can be shown in the agenda.
    """

    model = Topic()
    schema = DefaultSchema(Topic()).get_update_schema(
        properties=["title", "text", "attachment_ids", "tag_ids"]
    )
