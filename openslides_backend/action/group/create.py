from ...models.models import Group
from ..default_schema import DefaultSchema
from ..generics import CreateAction
from ..register import register_action


@register_action("group.create")
class GroupCreate(CreateAction):
    """
    Action to create a group.
    """

    model = Group()
    schema = DefaultSchema(Group()).get_create_schema(
        required_properties=["name", "meeting_id"],
        optional_properties=["permissions"],
    )
