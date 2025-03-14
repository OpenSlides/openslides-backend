from typing import Any

from ....models.models import Committee
from ....permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ....permissions.permission_helper import has_committee_management_level
from ....shared.exceptions import (
    ActionException,
    MissingPermission,
    ProtectedModelsException,
)
from ....shared.patterns import fqid_from_collection_and_id, id_from_fqid
from ....shared.util import ONE_ORGANIZATION_ID
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("committee.delete")
class CommitteeDeleteAction(DeleteAction):
    """
    Action to delete a committee.
    """

    model = Committee()
    schema = DefaultSchema(Committee()).get_delete_schema()
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True

    def check_permissions(self, instance: dict[str, Any]) -> None:
        if not has_committee_management_level(
            self.datastore,
            self.user_id,
            CommitteeManagementLevel.CAN_MANAGE,
            instance["id"],
        ):
            raise MissingPermission(
                {
                    OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION: ONE_ORGANIZATION_ID,
                    CommitteeManagementLevel.CAN_MANAGE: instance["id"],
                }
            )

    def base_update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        to_delete = self.datastore.get(
            fqid_from_collection_and_id("committee", instance["id"]), ["child_ids"]
        )
        if to_delete.get("child_ids"):
            raise ActionException(
                f"Can't delete committee {instance['id']} since it has subcommittees"
            )
        try:
            return super().base_update_instance(instance)
        except ProtectedModelsException as e:
            meeting_ids = [id_from_fqid(fqid) for fqid in e.fqids]
            count = len(meeting_ids)
            meetings_verbose = ", ".join(str(id_) for id_ in meeting_ids[:3])
            if count > 3:
                meetings_verbose += ", .."

            if count == 1:
                msg = f"This committee has still a meeting {meetings_verbose}."
            else:
                msg = f"This committee has still meetings {meetings_verbose}."
            msg += " Please remove all meetings before deletion."
            raise ActionException(msg)
