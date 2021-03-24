from ....models.models import Group
from ....permissions.permissions import Permissions
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("group.create")
class GroupCreate(CreateAction):
    """
    Action to create a group.
    """

    model = Group()
    schema = DefaultSchema(Group()).get_create_schema(
        required_properties=["name", "meeting_id"],
        optional_properties=[
            "permissions",
        ],
    )
    permission = Permissions.User.CAN_MANAGE
