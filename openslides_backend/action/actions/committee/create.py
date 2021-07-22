from typing import Any, Dict, List

from ....models.models import Committee
from ....permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.schema import id_list_schema
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..user.update import UserUpdate
from .committee_common_mixin import CommitteeCommonCreateUpdateMixin


@register_action("committee.create")
class CommitteeCreate(CommitteeCommonCreateUpdateMixin, CreateAction):
    """
    Action to create committees.
    """

    model = Committee()
    schema = DefaultSchema(Committee()).get_create_schema(
        required_properties=["organization_id", "name"],
        optional_properties=[
            "description",
            "user_ids",
            "organization_tag_ids",
            "forward_to_committee_ids",
            "receive_forwardings_from_committee_ids",
        ],
        additional_optional_fields={"manager_ids": id_list_schema},
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        if "manager_ids" in instance:
            manager_ids = instance.pop("manager_ids")
            action_data: List[Dict[str, Any]] = []
            for manager_id in manager_ids:
                manager = self.datastore.get(
                    FullQualifiedId(Collection("user"), manager_id), ["committee_ids"]
                )
                action_data.append(
                    {
                        "id": manager_id,
                        "committee_$_management_level": {
                            str(instance["id"]): CommitteeManagementLevel.CAN_MANAGE,
                        },
                        "committee_ids": manager.get("committee_ids", [])
                        + [instance["id"]],
                    }
                )
            self.apply_instance(instance)
            self.execute_other_action(UserUpdate, action_data)
        return instance
