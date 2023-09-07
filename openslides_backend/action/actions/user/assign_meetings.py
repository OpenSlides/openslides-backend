from typing import Any, Dict, Optional, Set

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import id_list_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionResultElement
from ..meeting_user.helper_mixin import MeetingUserHelperMixin
from ..meeting_user.update import MeetingUserUpdate


@register_action("user.assign_meetings")
class UserAssignMeetings(MeetingUserHelperMixin, UpdateAction):
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
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS
    use_meeting_ids_for_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        user_id = instance["id"]
        meeting_ids = set(instance.pop("meeting_ids"))
        group_name = instance.pop("group_name")
        meeting_to_group = {}
        meeting_ids_of_user_in_group: Set[int] = set()
        groups_meeting_ids: Set[int] = set()
        meeting_to_meeting_user: Dict[int, Dict[str, Any]] = {}
        user = self.datastore.get(
            fqid_from_collection_and_id("user", user_id),
            [
                "meeting_ids",
            ],
        )
        user_meeting_ids = set(user.get("meeting_ids", []))
        for meeting_id in meeting_ids:
            meeting_user = (
                self.get_meeting_user(meeting_id, user_id, ["id", "group_ids"]) or {}
            )
            meeting_to_meeting_user[meeting_id] = meeting_user
            filter_ = And(
                FilterOperator("name", "=", group_name),
                FilterOperator("meeting_id", "=", meeting_id),
            )
            groups = self.datastore.filter("group", filter_, ["meeting_id", "user_ids"])
            groups_meeting_ids.update(
                set(group["meeting_id"] for group in groups.values())
            )
            for key, group in groups.items():
                meeting_to_group[group["meeting_id"]] = key
            meeting_ids_of_user_in_group.update(
                group["meeting_id"]
                for group in groups.values()
                if meeting_user.get("id") in (group.get("meeting_user_ids") or [])
            )
        # Now split the meetings in the 3 categories
        self.success = groups_meeting_ids
        success_update = self.success.difference(meeting_ids_of_user_in_group)
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
            raise ActionException(
                f"Didn't find a group with groupname {group_name} in any meeting."
            )

        # fill the instance for the update
        for meeting_id in success_update:
            meeting_user = meeting_to_meeting_user[meeting_id]
            if not meeting_user.get("id"):
                meeting_user = {
                    "id": self.create_or_get_meeting_user(meeting_id, user_id)
                }
            self.execute_other_action(
                MeetingUserUpdate,
                [
                    {
                        "id": meeting_user["id"],
                        "group_ids": list(
                            set(meeting_user.get("group_ids") or []).union(
                                set([meeting_to_group[meeting_id]])
                            )
                        ),
                    }
                ],
            )
        for meeting_id in self.standard_meeting_ids:
            meeting_user = meeting_to_meeting_user[meeting_id]
            if not meeting_user.get("id"):
                meeting_user = {
                    "id": self.create_or_get_meeting_user(meeting_id, user_id)
                }
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", meeting_id), ["default_group_id"]
            )
            self.execute_other_action(
                MeetingUserUpdate,
                [
                    {
                        "id": meeting_user["id"],
                        "group_ids": list(
                            set(meeting_user.get("group_ids") or []).union(
                                set([meeting["default_group_id"]])
                            )
                        ),
                    }
                ],
            )

        return instance

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        result = {}
        result["succeeded"] = list(self.success)
        result["standard_group"] = list(self.standard_meeting_ids)
        result["nothing"] = list(self.nothing_meeting_ids)
        return result
