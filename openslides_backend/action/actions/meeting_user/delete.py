from typing import Any

from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ....models.models import MeetingUser
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..user.conditional_speaker_cascade_mixin import (
    ConditionalSpeakerCascadeMixinHelper,
)
from .base_delete import MeetingUserBaseDelete


@register_action("meeting_user.delete", action_type=ActionType.BACKEND_INTERNAL)
class MeetingUserDelete(ConditionalSpeakerCascadeMixinHelper, MeetingUserBaseDelete):
    """
    Action to delete a meeting user.
    """

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        meeting_user = self.datastore.get(
            fqid_from_collection_and_id("meeting_user", instance["id"]),
            ["speaker_ids", "user_id", "meeting_id"],
        )
        speaker_ids = meeting_user.get("speaker_ids", [])
        self.conditionally_delete_speakers(speaker_ids)
        self.remove_presence(meeting_user["user_id"], meeting_user["meeting_id"])

        return super().update_instance(instance)
