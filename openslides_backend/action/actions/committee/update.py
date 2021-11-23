from typing import Any, Dict, Set

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
from ....shared.filters import FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.schema import id_list_schema
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
            "forward_to_committee_ids",
            "receive_forwardings_from_committee_ids",
            "organization_tag_ids",
        ],
        additional_optional_fields={"manager_ids": id_list_schema},
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        if instance.get("template_meeting_id"):
            self.check_meeting_in_committee(
                instance["template_meeting_id"], instance["id"]
            )
        if instance.get("default_meeting_id"):
            self.check_meeting_in_committee(
                instance["default_meeting_id"], instance["id"]
            )

        if "manager_ids" in instance:
            old_manager_ids = self._get_old_manager_ids(instance["id"])
            self.update_managers(instance, old_manager_ids)
        return instance

    def check_meeting_in_committee(self, meeting_id: int, committee_id: int) -> None:
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), meeting_id), ["committee_id"]
        )
        if meeting.get("committee_id") != committee_id:
            raise ActionException(
                f"Meeting {meeting_id} does not belong to committee {committee_id}"
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

    def _get_old_manager_ids(self, committee_id: int) -> Set[int]:
        filter_ = FilterOperator(
            f"committee_${committee_id}_management_level",
            "=",
            CommitteeManagementLevel.CAN_MANAGE,
        )
        old_manager = self.datastore.filter(Collection("user"), filter_, ["id"])
        return set(id_ for id_ in old_manager)
