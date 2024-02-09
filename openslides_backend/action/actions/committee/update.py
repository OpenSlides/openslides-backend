from typing import Any

from ....models.models import Committee
from ....permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ....permissions.permission_helper import (
    has_committee_management_level,
    has_organization_management_level,
)
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.patterns import fqid_from_collection_and_id
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
            "default_meeting_id",
            "forward_to_committee_ids",
            "receive_forwardings_from_committee_ids",
            "organization_tag_ids",
            "manager_ids",
            "external_id",
        ],
    )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        if instance.get("default_meeting_id"):
            self.check_meeting_in_committee(
                instance["default_meeting_id"], instance["id"]
            )
        return instance

    def check_meeting_in_committee(self, meeting_id: int, committee_id: int) -> None:
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", meeting_id),
            ["committee_id"],
            lock_result=False,
        )
        if meeting.get("committee_id") != committee_id:
            raise ActionException(
                f"Meeting {meeting_id} does not belong to committee {committee_id}"
            )

    def check_permissions(self, instance: dict[str, Any]) -> None:
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
                    "forward_to_committee_ids",
                    "receive_forwardings_from_committee_ids",
                    "manager_ids",
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
