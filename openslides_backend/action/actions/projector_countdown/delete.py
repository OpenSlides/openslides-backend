from typing import Any

from ....models.models import ProjectorCountdown
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projector_countdown.delete")
class ProjectorCountdownDelete(DeleteAction):
    """
    Action to delete a projector countdown.
    """

    model = ProjectorCountdown()
    schema = DefaultSchema(ProjectorCountdown()).get_delete_schema()
    permission = Permissions.Projector.CAN_MANAGE

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        projector_countdown = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            [
                "used_as_list_of_speakers_countdown_meeting_id",
                "used_as_poll_countdown_meeting_id",
            ],
            lock_result=False,
        )
        meeting_id = projector_countdown.get(
            "used_as_list_of_speakers_countdown_meeting_id"
        ) or projector_countdown.get("used_as_poll_countdown_meeting_id")
        if meeting_id and not self.is_meeting_deleted(meeting_id):
            raise ActionException(
                "List of speakers or poll countdown is not allowed to delete."
            )

        return instance
