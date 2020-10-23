from typing import Any, Dict

from ...models.models import User
from ...shared.exceptions import ActionException
from ..base import Action


class TemporaryUserMixin(Action):
    def update_instance_temporary_user(
        self, instance: Dict[str, Any]
    ) -> Dict[str, Any]:
        present_in_meeting_ids = instance.get("is_present_in_meeting_ids")
        if present_in_meeting_ids and any(
            id != instance["meeting_id"] for id in present_in_meeting_ids
        ):
            raise ActionException(
                "A temporary user can only be present in its respective meeting."
            )
        if "group_ids" in instance:
            self.check_equal_fields(
                User.group__ids, instance, "group_ids", ["meeting_id"]
            )
            group_ids = instance.pop("group_ids")
            instance[f"group_${instance['meeting_id']}_ids"] = group_ids
        return instance
