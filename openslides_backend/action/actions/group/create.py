from typing import Any

from ....models.models import Group
from ....permissions.permission_helper import filter_surplus_permissions
from ....permissions.permissions import Permissions
from ...generics.create import CreateAction
from ...mixins.weight_mixin import WeightMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .group_mixin import GroupMixin


@register_action("group.create")
class GroupCreate(GroupMixin, WeightMixin, CreateAction):
    """
    Action to create a group.
    """

    model = Group()
    schema = DefaultSchema(Group()).get_create_schema(
        required_properties=["name", "meeting_id"],
        optional_properties=["permissions", "external_id"],
    )
    permission = Permissions.User.CAN_MANAGE

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        if instance.get("permissions"):
            instance["permissions"] = filter_surplus_permissions(
                instance["permissions"]
            )
        instance["weight"] = self.get_weight(instance["meeting_id"])
        return instance
