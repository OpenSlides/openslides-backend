from typing import Any, Dict

from ....models.models import Speaker
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import CheckSpeechState


@register_action("speaker.update")
class SpeakerUpdate(UpdateAction, CheckSpeechState):
    model = Speaker()
    schema = DefaultSchema(Speaker()).get_update_schema(["speech_state"])
    permission = Permissions.ListOfSpeakers.CAN_MANAGE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        speaker = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            ["speech_state", "meeting_id"],
        )
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), speaker["meeting_id"]),
            [
                "list_of_speakers_can_set_contribution_self",
                "list_of_speakers_enable_pro_contra_speech",
            ],
        )
        has_can_manage = has_perm(
            self.datastore,
            self.user_id,
            Permissions.ListOfSpeakers.CAN_MANAGE,
            speaker["meeting_id"],
        )
        allowed_self_contribution = has_can_manage or meeting.get(
            "list_of_speakers_can_set_contribution_self"
        )
        allowed_pro_contra = meeting.get("list_of_speakers_enable_pro_contra_speech")
        if speaker.get("speech_state") == instance.get("speech_state"):
            pass
        elif instance.get("speech_state") in ("contribution", "pro", "contra"):
            self.check_speech_state(instance, meeting_id=speaker["meeting_id"])
        elif (
            speaker.get("speech_state") == "contribution"
            and instance.get("speech_state") is None
        ):
            if not allowed_self_contribution:
                raise ActionException("Contribution speech is not allowed.")
        elif (
            speaker.get("speech_state") in ["pro", "contra"]
            and instance.get("speech_state") is None
        ):
            if not allowed_pro_contra:
                raise ActionException("Pro/Contra is not enabled")
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        speaker = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            ["user_id", "meeting_id"],
        )
        if speaker.get("user_id") == self.user_id and has_perm(
            self.datastore,
            self.user_id,
            Permissions.ListOfSpeakers.CAN_SEE,
            speaker["meeting_id"],
        ):
            return
        super().check_permissions(instance)
