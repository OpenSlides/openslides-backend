from typing import Any, Dict

from ....models.models import Group
from ....permissions.permission_helper import filter_surplus_permissions
from ....permissions.permissions import Permissions
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("group.update")
class GroupUpdateAction(UpdateAction):
    """
    Action to update a group.
    """

    model = Group()
    schema = DefaultSchema(Group()).get_update_schema(
        optional_properties=["name", "permissions"]
    )
    permission = Permissions.User.CAN_MANAGE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if "permissions" in instance:
            instance["permissions"] = filter_surplus_permissions(
                instance["permissions"]
            )
        return instance
