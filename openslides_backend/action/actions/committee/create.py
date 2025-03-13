from typing import Any

from ....models.models import Committee
from ....permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ....permissions.permission_helper import has_committee_management_level
from ....shared.exceptions import MissingPermission
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.util import ONE_ORGANIZATION_ID
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
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
            "organization_tag_ids",
            "forward_to_committee_ids",
            "receive_forwardings_from_committee_ids",
            "manager_ids",
            "external_id",
            "parent_id",
        ],
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION

    def check_permissions(self, instance: dict[str, Any]) -> None:
        if "parent_id" in instance:
            if not has_committee_management_level(
                self.datastore,
                self.user_id,
                CommitteeManagementLevel.CAN_MANAGE,
                instance["parent_id"],
            ):
                raise MissingPermission(
                    {
                        OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION: ONE_ORGANIZATION_ID,
                        CommitteeManagementLevel.CAN_MANAGE: instance["parent_id"],
                    }
                )
            return
        return super().check_permissions(instance)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        if "parent_id" in instance:
            instance["all_parent_ids"] = [
                *self.datastore.get(
                    fqid_from_collection_and_id("committee", instance["parent_id"]),
                    ["all_parent_ids"],
                ).get("all_parent_ids", []),
                instance["parent_id"],
            ]
        return super().update_instance(instance)
