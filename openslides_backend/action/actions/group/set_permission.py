from typing import Any, Dict

from ....models.models import Group
from ....shared.patterns import FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


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

    def get_updated_instances(self, payload: ActionData) -> ActionData:
        for instance in payload:
            new_instance = self.update_one_instance(instance)
            if new_instance.get("permissions") is None:
                continue
            yield new_instance

    def update_one_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        set_ = instance.pop("set")
        permission = instance.pop("permission")
        group = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]), ["permissions"]
        )
        if set_ is True and permission not in group["permissions"]:
            instance["permissions"] = group["permissions"]
            instance["permissions"].append(permission)
        elif set_ is False and permission in group["permissions"]:
            instance["permissions"] = group["permissions"]
            instance["permissions"].remove(permission)
        return instance
