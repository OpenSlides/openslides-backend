from typing import Any, Dict, Optional

from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...action import Action


class CheckSpeechState(Action):
    def check_speech_state(
        self, instance: Dict[str, Any], meeting_id: Optional[int] = None
    ) -> None:
        # check speech_state
        if meeting_id is None:
            meeting_id = instance["meeting_id"]
        if instance.get("speech_state") in ("pro", "contra"):
            meeting = self.datastore.get(
                FullQualifiedId(Collection("meeting"), meeting_id),
                ["list_of_speakers_enable_pro_contra_speech"],
            )
            if not meeting.get("list_of_speakers_enable_pro_contra_speech"):
                raise ActionException("Pro or contra speech is not enabled.")
        if instance.get("speech_state") == "contribution":
            meeting = self.datastore.get(
                FullQualifiedId(Collection("meeting"), meeting_id),
                ["list_of_speakers_can_set_contribution_self"],
            )
            has_los_can_manage = has_perm(
                self.datastore,
                self.user_id,
                Permissions.ListOfSpeakers.CAN_MANAGE,
                meeting_id,
            )
            if not has_los_can_manage and not meeting.get(
                "list_of_speakers_can_set_contribution_self"
            ):
                raise ActionException("Contribution speech is not allowed.")
