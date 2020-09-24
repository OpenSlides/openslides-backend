from ...models.models import Topic
from ..action import register_action
from ..default_schema import DefaultSchema
from ..generics import DeleteAction


@register_action("topic.delete")
class TopicDelete(DeleteAction):
    """
    Action to delete simple topics that can be shown in the agenda.
    """

    model = Topic()
    schema = DefaultSchema(Topic()).get_delete_schema()
