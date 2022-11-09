from typing import Any, Dict

from ....models.models import MeetingUser
from ....permissions.permissions import Permissions
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting_user.create")
class MeetingUserCreate(CreateAction):
    """
    Action to create a meeting user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_create_schema(
        required_properties=["user_id", "meeting_id"],
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
            if self.user_id == instance["user_id"]:
                return
        super().check_permissions(instance)
