from typing import Any, Dict

from ....models.models import ProjectorCountdown
from ....shared.exceptions import ActionException
from ....shared.patterns import FullQualifiedId
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

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        projector_countdown = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            [
                "used_as_list_of_speaker_countdown_meeting_id",
                "used_as_poll_countdown_meeting_id",
            ],
        )
        if projector_countdown.get(
            "used_as_list_of_speaker_countdown_meeting_id"
        ) or projector_countdown.get("used_as_poll_countdown_meeting_id"):
            raise ActionException(
                "List of speakers or poll countdown is not allowed to delete."
            )

        return instance
