from typing import Any, Dict

from ....models.models import MeetingUser
from ....permissions.permissions import Permissions
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting_user.update")
class MeetingUserUpdate(UpdateAction):
    """
    Action to update a meeting_user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_update_schema(
        optional_properties=[
            "comment",
            "number",
            "structure_level",
            "about_me",
            "vote_weight",
        ],
    )
    permission = Permissions.User.CAN_MANAGE

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if "about_me" in instance and not any(
            field in instance
            for field in ("comment", "number", "structure_level", "vote_weight")
        ):
            meeting_user = self.datastore.get(
                fqid_from_collection_and_id("meeting_user", instance["id"]),
                ["user_id"],
                lock_result=False,
            )
            if self.user_id == meeting_user["user_id"]:
                return
        super().check_permissions(instance)
