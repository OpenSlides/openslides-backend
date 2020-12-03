from typing import Any, Dict

from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...action import BaseAction


class CheckTemporaryMixin(BaseAction):
    """
    Mixin to provide check_for_temporary().
    """

    def check_for_temporary(self, instance: Dict[str, Any]) -> None:
        if "meeting_id" not in instance:
            db_instance = self.datastore.get(
                FullQualifiedId(Collection("user"), instance["id"]), ["meeting_id"]
            )
            instance["meeting_id"] = db_instance.get("meeting_id")
        if not instance.get("meeting_id"):
            raise ActionException(f"User {instance['id']} is not temporary.")
