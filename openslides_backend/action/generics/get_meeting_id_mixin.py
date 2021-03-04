from typing import Any, Dict

from ...shared.patterns import FullQualifiedId
from ..action import Action


class GetMeetingIdMixin(Action):
    """
    Mixin to easily return the meeting id for update and delete actions.
    """

    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        if instance.get("meeting_id"):
            return instance["meeting_id"]
        else:
            db_instance = self.fetch_model(
                FullQualifiedId(self.model.collection, instance["id"]), ["meeting_id"]
            )
            return db_instance["meeting_id"]
