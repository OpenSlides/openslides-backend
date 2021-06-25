from typing import Any, Dict

from ....models.models import Committee
from ....permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ....permissions.permission_helper import (
    has_committee_management_level,
    has_organization_management_level,
)
from ....shared.exceptions import MissingPermission
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .committee_common_mixin import CommitteeCommonCreateUpdateMixin


@register_action("committee.update")
class CommitteeUpdateAction(CommitteeCommonCreateUpdateMixin, UpdateAction):
    """
    Action to update a committee.
    """

    model = Committee()
    schema = DefaultSchema(Committee()).get_update_schema(
        optional_properties=[
            "name",
            "description",
            "template_meeting_id",
            "default_meeting_id",
            "user_ids",
            "forward_to_committee_ids",
            "receive_forwardings_from_committee_ids",
            "organization_tag_ids",
        ]
    )

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if has_organization_management_level(
            self.datastore,
            self.user_id,
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        ):
            return

        if any(
            [
                field in instance
                for field in [
                    "user_ids",
                    "forward_to_committee_ids",
                    "receive_forwardings_from_committee_ids",
                ]
            ]
        ):
            raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION)

        if has_committee_management_level(
            self.datastore,
            self.user_id,
            CommitteeManagementLevel.CAN_MANAGE,
            instance["id"],
        ):
            return

        raise MissingPermission(
            {
                OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION: 1,
                CommitteeManagementLevel.CAN_MANAGE: instance["id"],
            }
        )
