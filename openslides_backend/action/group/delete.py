from ...models.models import Group
from ..default_schema import DefaultSchema
from ..generics import DeleteAction
from ..register import register_action


@register_action("group.delete")
class GroupDeleteAction(DeleteAction):
    """
    Action to delete a group.
    """

    model = Group()
    schema = DefaultSchema(Group()).get_delete_schema()
