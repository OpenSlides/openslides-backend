from typing import Any, Dict

from ....models.models import MeetingUser
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...mixins.extend_history_mixin import ExtendHistoryMixin
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .helper_mixin import MeetingUserHelperMixin
from .mixin import MeetingUserMixin


@register_action("meeting_user.set_data", action_type=ActionType.BACKEND_INTERNAL)
class MeetingUserSetData(
    MeetingUserMixin,
    ExtendHistoryMixin,
    MeetingUserHelperMixin,
    UpdateAction,
):
    """
    Action to create, update or delete a meeting_user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_create_schema(
        optional_properties=[
            "id",
            "meeting_id",
            "user_id",
            "comment",
            "number",
            "structure_level",
            "about_me",
            "vote_weight",
            "vote_delegated_to_id",
            "vote_delegations_from_ids",
            "group_ids",
        ],
    )
    extend_history_to = "user_id"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_id = instance.get("meeting_id")
        user_id = instance.pop("user_id", None)
        if instance.get("id"):
            fqid = fqid_from_collection_and_id("meeting_user", instance["id"])
            meeting_user = self.datastore.get(
                fqid, ["meeting_id", "user_id"], raise_exception=True
            )
            if meeting_id:
                assert (
                    meeting_id == meeting_user["meeting_id"]
                ), "Not permitted to change meeting_id."
            if user_id:
                assert (
                    user_id == meeting_user["user_id"]
                ), "Not permitted to change user_id."
        elif meeting_id and user_id:
            instance["id"] = self.create_or_get_meeting_user(meeting_id, user_id)
        # MeetingUserMixin needs the meeting_id in "create" case
        instance = super().update_instance(instance)
        instance.pop("meeting_id", None)
        return instance

    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        if not instance.get("id") and (
            not instance.get("user_id") or not instance.get("meeting_id")
        ):
            raise ActionException(
                "Identifier for meeting_user instance required, but neither id nor meeting_id/user_id is given."
            )
        return super().get_meeting_id(instance)
