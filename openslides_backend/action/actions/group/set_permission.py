from typing import Any, Dict

from ....models.models import Group
from ....permissions.permission_helper import filter_surplus_permissions
from ....permissions.permissions import Permissions
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("group.set_permission")
class GroupSetPermissionAction(UpdateAction):
    """
    Action to set permission of a group.
    """

    model = Group()
    schema = DefaultSchema(Group()).get_update_schema(
        additional_required_fields={
            "set": {"type": "boolean"},
            "permission": {"type": "string"},
        }
    )
    permission = Permissions.User.CAN_MANAGE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        set_ = instance.pop("set")
        permission = instance.pop("permission")
        group = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["permissions"],
        )
        group_permissions = group.get("permissions") or []
        if set_ is True and permission not in group_permissions:
            instance["permissions"] = group_permissions
            instance["permissions"].append(permission)
            instance["permissions"] = filter_surplus_permissions(
                instance["permissions"]
            )
        elif set_ is False and permission in group_permissions:
            instance["permissions"] = group_permissions
            instance["permissions"].remove(permission)
        return instance
