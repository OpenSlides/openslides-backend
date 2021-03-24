from ....models.models import Group
from ....permissions.permissions import Permissions
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("group.delete")
class GroupDeleteAction(DeleteAction):
    """
    Action to delete a group.
    """

    model = Group()
    schema = DefaultSchema(Group()).get_delete_schema()
    permission = Permissions.User.CAN_MANAGE
