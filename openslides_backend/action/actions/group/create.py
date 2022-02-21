from typing import Any, Dict

from ....models.models import Group
from ....permissions.permission_helper import filter_surplus_permissions
from ....permissions.permissions import Permissions
from ....shared.filters import FilterOperator
from ...action import original_instances
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


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

    @original_instances
    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        self.weight_map: Dict[int, int] = {}
        return super().get_updated_instances(action_data)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if instance.get("permissions"):
            instance["permissions"] = filter_surplus_permissions(
                instance["permissions"]
            )
        self.set_weight(instance)
        return instance

    def set_weight(self, instance: Dict[str, Any]) -> None:
        meeting_id = instance["meeting_id"]
        if meeting_id in self.weight_map:
            max_weight = self.weight_map[meeting_id]
        else:
            filter_ = FilterOperator("meeting_id", "=", meeting_id)
            max_weight = (
                self.datastore.max(self.model.collection, filter_, "weight", "int") or 0
            )
        self.weight_map[meeting_id] = max_weight + 1
        instance["weight"] = self.weight_map[meeting_id]
