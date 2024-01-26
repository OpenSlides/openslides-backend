from typing import Any, Dict, Optional

from openslides_backend.shared.patterns import fqid_from_collection_and_id
from openslides_backend.shared.typing import HistoryInformation

from ....models.models import MeetingUser
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..user.conditional_speaker_cascade_mixin import (
    ConditionalSpeakerCascadeMixinHelper,
)


@register_action("meeting_user.delete", action_type=ActionType.BACKEND_INTERNAL)
class MeetingUserDelete(ConditionalSpeakerCascadeMixinHelper, DeleteAction):
    """
    Action to delete a meeting user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_delete_schema()

    def get_history_information(self) -> Optional[HistoryInformation]:
        users = self.get_instances_with_fields(["user_id", "meeting_id"])
        return {
            fqid_from_collection_and_id("user", user["user_id"]): [
                "Participant removed from meeting {}",
                fqid_from_collection_and_id("meeting", user["meeting_id"]),
            ]
            for user in users
        }

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_user = self.datastore.get(
            fqid_from_collection_and_id("meeting_user", instance["id"]), ["speaker_ids"]
        )
        speaker_ids = meeting_user.get("speaker_ids", [])
        self.conditionally_delete_speakers(speaker_ids)

        return super().update_instance(instance)
