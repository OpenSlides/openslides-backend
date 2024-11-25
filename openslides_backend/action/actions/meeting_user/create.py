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
            fqids_per_collection = {
                collection_name: [
                    fqid_from_collection_and_id(
                        collection_name,
                        _id,
                    )
                    for _id in ids
                ]
                for collection_name in ["group", "structure_level"]
                if (ids := instance.get(f"{collection_name}_ids"))
            }
            instance_information.append(
                self.compose_history_string(list(fqids_per_collection.items()))
            )
            for collection_name, fqids in fqids_per_collection.items():
                instance_information.extend(fqids)
            instance_information.append(
                fqid_from_collection_and_id("meeting", instance["meeting_id"]),
            )
            information[fqid_from_collection_and_id("user", instance["user_id"])] = (
                instance_information
            )
        return information

    def compose_history_string(
        self, fqids_per_collection: list[tuple[str, list[str]]]
    ) -> str:
        """
        Composes a string of the shape:
        Participant added to groups {}, {} and structure levels {} in meeting {}.
        """
        middle_sentence_parts = [
            " ".join(
                [  # prefix and to collection name if it's not the first in list
                    ("and " if collection_name != fqids_per_collection[0][0] else "")
                    + collection_name.replace("_", " ")  # replace for human readablity
                    + ("s" if len(fqids) != 1 else ""),  # plural s
                    ", ".join(["{}" for _ in range(len(fqids))]),
                ]
            )
            for collection_name, fqids in fqids_per_collection
        ]
        return " ".join(
            [
                "Participant added to",
                *middle_sentence_parts,
                ("in " if fqids_per_collection else "") + "meeting {}.",
            ]
        )
