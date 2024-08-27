from typing import Any

from openslides_backend.shared.exceptions import ActionException
from openslides_backend.shared.patterns import fqid_from_collection_and_id
from openslides_backend.shared.typing import HistoryInformation

from ....models.models import MeetingUser
from ...generics.create import CreateAction
from ...mixins.meeting_user_helper import get_meeting_user_filter
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .history_mixin import MeetingUserHistoryMixin
from .mixin import (
    CheckLockOutPermissionMixin,
    MeetingUserGroupMixin,
    meeting_user_standard_fields,
)


@register_action("meeting_user.create", action_type=ActionType.BACKEND_INTERNAL)
class MeetingUserCreate(
    MeetingUserHistoryMixin,
    CreateAction,
    MeetingUserGroupMixin,
    CheckLockOutPermissionMixin,
):
    """
    Action to create a meeting user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_create_schema(
        required_properties=["user_id", "meeting_id"],
        optional_properties=[
            "about_me",
            "group_ids",
            *meeting_user_standard_fields,
        ],
    )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        if self.datastore.exists(
            "meeting_user",
            get_meeting_user_filter(instance["meeting_id"], instance["user_id"]),
        ):
            raise ActionException(
                f"MeetingUser instance with user {instance['user_id']} and meeting {instance['meeting_id']} already exists"
            )
        self.check_locking_status(instance["meeting_id"], instance, instance["user_id"])
        return super().update_instance(instance)

    def get_history_information(self) -> HistoryInformation | None:
        information = {}
        for instance in self.instances:
            instance_information = []
            if "group_ids" in instance:
                if len(instance["group_ids"]) == 1:
                    instance_information.extend(
                        [
                            "Participant added to group {} in meeting {}",
                            fqid_from_collection_and_id(
                                "group", instance["group_ids"][0]
                            ),
                        ]
                    )
                else:
                    instance_information.append(
                        "Participant added to multiple groups in meeting {}",
                    )
            else:
                instance_information.append(
                    "Participant added to meeting {}",
                )
            instance_information.append(
                fqid_from_collection_and_id("meeting", instance["meeting_id"]),
            )
            information[fqid_from_collection_and_id("user", instance["user_id"])] = (
                instance_information
            )
        return information
