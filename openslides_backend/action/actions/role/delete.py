from ....models.models import Role
from ...action import PERMISSION_SPECIAL_CASE
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("role.delete")
class RoleDeleteAction(DeleteAction):
    """
    Action to delete a role.
    """

    model = Role()
    schema = DefaultSchema(Role()).get_delete_schema()
    permission_description = PERMISSION_SPECIAL_CASE
