from typing import Any

from ....models.models import Committee
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.exceptions import ActionException, ProtectedModelsException
from ....shared.patterns import id_from_fqid
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

    def base_update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
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
