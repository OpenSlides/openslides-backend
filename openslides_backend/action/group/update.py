from ...models.models import Group
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action


@register_action("group.update")
class GroupUpdateAction(UpdateAction):
    """
    Action to update a group.
    """

    model = Group()
    schema = DefaultSchema(Group()).get_update_schema(optional_properties=["name"])
