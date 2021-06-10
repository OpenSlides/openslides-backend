from typing import Any, Dict

from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...action import Action


class ChatEnabledMixin(Action):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_id = instance.get("meeting_id")
        if not meeting_id:
            chat_group = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), ["meeting_id"]
            )
            meeting_id = chat_group["meeting_id"]
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), meeting_id),
            ["enable_chat"],
        )
        if not meeting.get("enable_chat"):
            raise ActionException("Chat is not enabled.")
        return instance
