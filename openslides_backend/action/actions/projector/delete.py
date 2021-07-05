from typing import Any, Dict

from ....models.models import Projector
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import FullQualifiedId
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..meeting.replace_projector_id import MeetingReplaceProjectorId


@register_action("projector.delete")
class ProjectorDelete(DeleteAction):
    """
    Action to delete a projector.
    """

    model = Projector()
    schema = DefaultSchema(Projector()).get_delete_schema()
    permission = Permissions.Projector.CAN_MANAGE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        projector = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            ["used_as_reference_projector_meeting_id", "meeting_id"],
        )
        if (
            meeting_id := projector.get("used_as_reference_projector_meeting_id")
        ) and not self.is_meeting_deleted(meeting_id):
            raise ActionException(
                "A used as reference projector is not allowed to delete."
            )

        payload = [{"id": projector.get("meeting_id"), "projector_id": instance["id"]}]
        self.execute_other_action(MeetingReplaceProjectorId, payload)
        return instance
