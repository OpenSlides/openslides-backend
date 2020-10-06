from ...models.models import Topic
from ..default_schema import DefaultSchema
from ..generics import DeleteAction
from ..register import register_action


@register_action("topic.delete")
class TopicDelete(DeleteAction):
    """
    Action to delete simple topics that can be shown in the agenda.
    """

    model = Topic()
    schema = DefaultSchema(Topic()).get_delete_schema()
