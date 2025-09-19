from typing import Any

from openslides_backend.action.mixins.check_unique_name_mixin import (
    CheckUniqueInContextMixin,
)

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ....permissions.permission_helper import get_failing_committee_management_levels
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.util import ONE_ORGANIZATION_ID


class CommitteeCommonCreateUpdateMixin(
    CheckUniqueInContextMixin, CheckForArchivedMeetingMixin
):
    def check_forwarding_fields(self, instance: dict[str, Any]) -> None:
        id_ = instance.get("id")
        forwarding_fields = [
            "forward_to_committee_ids",
            "receive_forwardings_from_committee_ids",
            "forward_agenda_to_committee_ids",
            "receive_agenda_forwardings_from_committee_ids",
        ]
        if id_:
            committee = self.datastore.get(
                fqid_from_collection_and_id("committee", id_),
                [*forwarding_fields, "manager_ids"],
            )
        else:
            committee = {}
        field_difference: set[int] = set()
        for field in forwarding_fields:
            if field in instance:
                field_set = set(instance.get(field, []))
                field_difference.update(
                    field_set.symmetric_difference(committee.get(field, []))
                )
        if field_difference:
            if fails := get_failing_committee_management_levels(
                self.datastore,
                self.user_id,
                list(field_difference),
            ):
                raise MissingPermission(
                    {
                        OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION: ONE_ORGANIZATION_ID,
                        CommitteeManagementLevel.CAN_MANAGE: set(fails),
                    }
                )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Check if own committee is forwarded or received explicitly,
        it may not be excluded by the opposite setting
        """
        instance = super().update_instance(instance)
        id_ = instance.get("id")
        motion_forwarding_fields = [
            "forward_to_committee_ids",
            "receive_forwardings_from_committee_ids",
        ]
        agenda_forwarding_fields = [
            "forward_agenda_to_committee_ids",
            "receive_agenda_forwardings_from_committee_ids",
        ]
        for message, fields in {
            "Forwarding or receiving to/from own must be configured in both directions!": motion_forwarding_fields,
            "Agenda forwarding or receiving to/from own must be configured in both directions!": agenda_forwarding_fields,
        }.items():
            if (
                not any(instance.get(field) is None for field in fields)
                and len({id_ in instance.get(field, []) for field in fields}) == 2
            ):
                raise ActionException(message)
        return instance

    def validate_instance(self, instance: dict[str, Any]) -> None:
        super().validate_instance(instance)
        if instance.get("external_id"):
            self.check_unique_in_context(
                "external_id",
                instance["external_id"],
                "The external_id of the committee is not unique.",
                instance.get("id"),
            )
