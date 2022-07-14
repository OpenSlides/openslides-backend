from typing import Any, Dict, Optional

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
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
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS

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
        meeting_to_group = {}
        for key, group in groups.items():
            meeting_to_group[group["meeting_id"]] = key

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

        if not success_update:
            raise ActionException(
                f"Didn't find a group with groupname {group_name} to assign to in any meeting."
            )

        # fill the instance for the update
        if success_update.union(self.standard_meeting_ids):
            instance["group_$_ids"] = {}
        for meeting_id in success_update:
            instance["group_$_ids"][meeting_id] = list(
                set(user.get(f"group_${meeting_id}_ids") or []).union(
                    set([meeting_to_group[meeting_id]])
                )
            )
        meetings = {}
        if self.standard_meeting_ids:
            get_many_request = GetManyRequest(
                "meeting", list(self.standard_meeting_ids), ["default_group_id"]
            )
            get_many_result = self.datastore.get_many([get_many_request])
            meetings = get_many_result.get("meeting", {})
        for meeting_id in self.standard_meeting_ids:
            meeting = meetings[meeting_id]
            instance["group_$_ids"][meeting_id] = [meeting["default_group_id"]]

        return instance

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        result = {}
        result["succeeded"] = list(self.success)
        result["standard_group"] = list(self.standard_meeting_ids)
        result["nothing"] = list(self.nothing_meeting_ids)
        return result
