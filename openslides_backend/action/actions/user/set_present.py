from typing import Any

from openslides_backend.shared.history_events import build_history_information_data
from openslides_backend.shared.typing import HistoryInformation

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....action.mixins.meeting_user_helper import get_meeting_user
from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import (
    has_committee_management_level,
    has_organization_management_level,
    has_perm,
)
from ....permissions.permissions import Permissions
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


@register_action("user.set_present")
class UserSetPresentAction(UpdateAction, CheckForArchivedMeetingMixin):
    """
    Action to set present.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        additional_required_fields={
            "present": {"type": "boolean"},
            "meeting_id": required_id_schema,
        }
    )

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        """
        update is_present_in_meeting_ids:
        add meeting_id if present is True.
        remove meeting_id if present is False.
        """
        self.base_history_information = {}
        for instance in action_data:
            meeting_id = instance.pop("meeting_id")
            present = instance.pop("present")
            user = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                ["is_present_in_meeting_ids", "meeting_ids"],
            )
            self.base_history_information[instance["id"]] = {
                "present": present,
                "meeting_id": meeting_id,
                "all_meeting_ids": user.get("meeting_ids", []),
            }
            if present:
                if meeting_id not in user.get("is_present_in_meeting_ids", []):
                    is_present = user.get("is_present_in_meeting_ids", []) + [
                        meeting_id
                    ]
                    instance["is_present_in_meeting_ids"] = is_present
                    self.base_history_information[instance["id"]][
                        "is_present_in_meeting_ids"
                    ] = is_present
                    yield instance
            elif present is False:
                is_present = user.get("is_present_in_meeting_ids", [])
                if meeting_id in is_present:
                    is_present.remove(meeting_id)
                    instance["is_present_in_meeting_ids"] = is_present
                    self.base_history_information[instance["id"]][
                        "is_present_in_meeting_ids"
                    ] = is_present
                    yield instance

    def check_permissions(self, instance: dict[str, Any]) -> None:
        if has_perm(
            self.datastore,
            self.user_id,
            Permissions.User.CAN_MANAGE_PRESENCE,
            instance["meeting_id"],
        ):
            return
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["meeting_id"]),
            ["committee_id", "users_allow_self_set_present", "locked_from_inside"],
            lock_result=False,
        )
        if not meeting.get("locked_from_inside"):
            if has_organization_management_level(
                self.datastore,
                self.user_id,
                OrganizationManagementLevel.CAN_MANAGE_USERS,
            ):
                return
            if has_committee_management_level(
                self.datastore,
                self.user_id,
                meeting["committee_id"],
            ):
                return
        if self.user_id == instance["id"] and meeting.get(
            "users_allow_self_set_present"
        ):
            return
        raise PermissionDenied("You are not allowed to set present.")

    def get_history_information(self) -> HistoryInformation | None:
        information: HistoryInformation = {}
        for user_id, data in self.base_history_information.items():
            present = data["present"]
            meeting_id = data["meeting_id"]
            information[fqid_from_collection_and_id(self.model.collection, user_id)] = (
                build_history_information_data(
                    [
                        f"Set {'not ' if not present else ''}present in meeting {{}}",
                        fqid_from_collection_and_id("meeting", meeting_id),
                    ],
                )
            )
            if meeting_id in data["all_meeting_ids"]:
                meeting_user = get_meeting_user(
                    self.datastore,
                    meeting_id,
                    user_id,
                    ["id"],
                )
                if meeting_user:
                    information[
                        fqid_from_collection_and_id("meeting_user", meeting_user["id"])
                    ] = build_history_information_data(
                        structured_information={"is_present": present}
                    )
        return information
