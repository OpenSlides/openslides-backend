from typing import Any

from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ...action import Action


class CheckSpeechState(Action):
    def check_speech_state(
        self,
        speaker: dict[str, Any],
        instance: dict[str, Any],
        meeting_id: int | None = None,
    ) -> None:
        # check speech_state
        if meeting_id is None:
            meeting_id = instance["meeting_id"]
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", meeting_id),
            [
                "list_of_speakers_can_set_contribution_self",
                "list_of_speakers_enable_pro_contra_speech",
            ],
            lock_result=False,
        )
        has_can_manage = has_perm(
            self.datastore,
            self.user_id,
            Permissions.ListOfSpeakers.CAN_MANAGE,
            meeting_id,
        )
        allowed_self_contribution = has_can_manage or meeting.get(
            "list_of_speakers_can_set_contribution_self"
        )
        allowed_pro_contra = meeting.get("list_of_speakers_enable_pro_contra_speech")
        if speaker.get("speech_state") == instance.get("speech_state"):
            pass
        elif instance.get("speech_state") == "contribution":
            if not allowed_self_contribution:
                raise ActionException("Self contribution is not allowed.")
        elif instance.get("speech_state") in ["pro", "contra"]:
            if not allowed_pro_contra:
                raise ActionException("Pro/Contra is not enabled.")
        elif (
            speaker.get("speech_state") == "contribution"
            and instance.get("speech_state") is None
        ):
            if not allowed_self_contribution:
                raise ActionException("Self contribution is not allowed.")
        elif (
            speaker.get("speech_state") in ["pro", "contra"]
            and instance.get("speech_state") is None
        ):
            if not allowed_pro_contra:
                raise ActionException("Pro/Contra is not enabled.")
