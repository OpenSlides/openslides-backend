from typing import Any, Dict, Optional

from ....models.models import User
from ....permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ....permissions.permission_helper import (
    has_committee_management_level,
    has_organization_management_level,
    has_perm,
)
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException, PermissionDenied
from ....shared.filters import And, FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionResultElement


@register_action("user.toggle_presence_by_number")
class UserTogglePresenceByNumber(UpdateAction):
    """
    Action to toggle the presence by number
    """

    model = User()
    schema = DefaultSchema(User()).get_default_schema(
        additional_required_fields={
            "number": {"type": "string"},
            "meeting_id": required_id_schema,
        }
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        update is_present_in_meeting_ids:
        """
        meeting_id = instance.pop("meeting_id")
        number = instance.pop("number")

        instance["id"] = self.find_user_to_number(meeting_id, number)

        user = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            ["is_present_in_meeting_ids"],
        )
        is_present = user.get("is_present_in_meeting_ids", [])
        if meeting_id not in is_present:
            instance["is_present_in_meeting_ids"] = user.get(
                "is_present_in_meeting_ids", []
            ) + [meeting_id]
        else:
            is_present.remove(meeting_id)
            instance["is_present_in_meeting_ids"] = is_present
        return instance

    def find_user_to_number(self, meeting_id: int, number: str) -> int:
        filter_ = FilterOperator(f"number_${meeting_id}", "=", number)
        result = self.datastore.filter(Collection("user"), filter_, ["id"])
        if len(result.keys()) == 1:
            return list(result.keys())[0]
        elif len(result.keys()) > 1:
            raise ActionException("Found more than one user with the number.")

        filter_ = And(
            FilterOperator(f"number_${meeting_id}", "=", ""),
            FilterOperator("default_number", "=", number),
        )
        result = self.datastore.filter(Collection("user"), filter_, ["id"])
        if len(result.keys()) == 1:
            return list(result.keys())[0]
        elif len(result.keys()) > 1:
            raise ActionException("Found more than one user with the default number.")
        raise ActionException("No user with this number found.")

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        return {"id": instance["id"]}

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            return
        if has_perm(
            self.datastore,
            self.user_id,
            Permissions.User.CAN_MANAGE,
            instance["meeting_id"],
        ):
            return
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), instance["meeting_id"]),
            ["committee_id"],
        )
        if has_committee_management_level(
            self.datastore,
            self.user_id,
            CommitteeManagementLevel.CAN_MANAGE,
            meeting["committee_id"],
        ):
            return
        raise PermissionDenied("You are not allowed to toggle presence by number.")
