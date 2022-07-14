from typing import Any, Dict, List, Optional

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import has_organization_management_level
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.filters import And, FilterOperator, Or
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import id_list_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionResultElement


@register_action("user.assign_meetings")
class UserAssignMeetings(UpdateAction):
    """
    Action to assign a user to multiple groups and meetings.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        additional_required_fields={
            "meeting_ids": {
                "description": "An array of meetings, in the user should be added to a group.",
                **id_list_schema,
            },
            "group_name": {"type": "string"},
        }
    )
    skip_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        user_id = instance["id"]
        meeting_ids = set(instance.pop("meeting_ids"))
        group_name = instance.pop("group_name")

        user = self.datastore.get(
            fqid_from_collection_and_id("user", user_id),
            [
                "meeting_ids",
                "group_$_ids",
                *[f"group_${meeting_id}_ids" for meeting_id in meeting_ids],
            ],
        )
        user_meeting_ids = set(user.get("meeting_ids", []))
        filter_ = And(
            FilterOperator("name", "=", group_name),
            Or(
                *[
                    FilterOperator("meeting_id", "=", meeting_id)
                    for meeting_id in meeting_ids
                ]
            ),
        )
        groups = self.datastore.filter("group", filter_, ["meeting_id", "user_ids"])
        groups_meeting_ids = set(group["meeting_id"] for group in groups.values())
        # Now split the meetings in the 3 categories
        self.success = groups_meeting_ids
        success_update = self.success.difference(user_meeting_ids)
        self.standard_meeting_ids = meeting_ids.difference(
            groups_meeting_ids
        ).difference(user_meeting_ids)
        self.nothing_meeting_ids = meeting_ids.difference(
            groups_meeting_ids
        ).intersection(user_meeting_ids)
        # check if all meetings are set into one category
        assert (
            self.success.union(self.standard_meeting_ids).union(
                self.nothing_meeting_ids
            )
            == meeting_ids
        )

        if not self.success:
            raise ActionException("Don't find a group with groupname in any meeting.")

        # fill the instance for the update
        if success_update.union(self.standard_meeting_ids):
            instance["group_$_ids"] = {}
        for meeting_id in success_update:
            instance["group_$_ids"][meeting_id] = list(
                set(user.get(f"group_${meeting_id}_ids") or []).union(
                    set(self.find_group_id(meeting_id, groups))
                )
            )
        for meeting_id in self.standard_meeting_ids:
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", meeting_id), ["default_group_id"]
            )
            instance["group_$_ids"][meeting_id] = [meeting["default_group_id"]]

        return instance

    def find_group_id(self, meeting_id: int, groups: Dict[int, Any]) -> List[int]:
        for group_id, group in groups.items():
            if group.get("meeting_id") == meeting_id:
                return [group_id]
        raise ActionException("Error, could not find group-id")

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        result = {}
        result["succeeded"] = list(self.success)
        result["standard_group"] = list(self.standard_meeting_ids)
        result["nothing"] = list(self.nothing_meeting_ids)
        return result

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if not has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_USERS)
        # Remove CML and perms checks here because of performance issues.
