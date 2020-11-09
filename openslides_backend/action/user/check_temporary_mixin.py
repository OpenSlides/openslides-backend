from typing import Any, Dict

from ...shared.exceptions import ActionException
from ...shared.patterns import Collection, FullQualifiedId
from ..base import BaseAction


class CheckTemporaryMixin(BaseAction):
    """
    Mixin to provide check_for_temporary().
    """

    def check_for_temporary(self, instance: Dict[str, Any]) -> None:
        user = self.datastore.get(
            FullQualifiedId(Collection("user"), instance["id"]), ["meeting_id"]
        )
        if not user.get("meeting_id"):
            raise ActionException(f"User {instance['id']} is not temporary.")
