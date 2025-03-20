from typing import Any

from ....models.models import User
from ....permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ....permissions.permission_helper import (
    has_committee_management_level,
    has_organization_management_level,
)
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException, MissingPermission
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

    def check_permissions(self, instance: dict[str, Any]) -> None:
        if (
            not has_organization_management_level(
                self.datastore,
                self.user_id,
                OrganizationManagementLevel.CAN_MANAGE_USERS,
            )
        ) and (meeting_ids := instance.get("meeting_ids")):
            meetings = self.datastore.get_many(
                [GetManyRequest("meeting", meeting_ids, ["committee_id"])],
                lock_result=False,
            )["meeting"]
            committee_ids = {
                meeting["committee_id"]
                for meeting in meetings.values()
                if meeting.get("committee_id")
            }
            committee_ids = {
                committee_id
                for committee_id in committee_ids
                if not has_committee_management_level(
                    self.datastore,
                    self.user_id,
                    CommitteeManagementLevel.CAN_MANAGE,
                    committee_id,
                )
            }
            if committee_ids:
                raise MissingPermission(
                    {CommitteeManagementLevel.CAN_MANAGE: committee_ids}
                )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        self.check_meetings(instance)
        user_id = instance["id"]
        meeting_ids = set(instance.pop("meeting_ids"))
        group_name = instance.pop("group_name")
        meeting_to_group = {}
        meeting_ids_of_user_in_group: set[int] = set()
        groups_meeting_ids: set[int] = set()
        meeting_to_meeting_user: dict[int, dict[str, Any]] = {}
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
                FilterOperator("anonymous_group_for_meeting_id", "=", None),
            )
            groups = self.datastore.filter(
                "group", filter_, ["meeting_id", "meeting_user_ids"]
            )
            groups_meeting_ids.update(
                {group["meeting_id"] for group in groups.values()}
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
                                {meeting_to_group[meeting_id]}
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
                                {meeting["default_group_id"]}
                            )
                        ),
                    }
                ],
            )

        return instance

    def check_meetings(self, instance: dict[str, Any]) -> None:
        if meeting_ids := instance.get("meeting_ids"):
            locked_meetings = [
                str(id_)
                for id_, meeting in self.datastore.get_many(
                    [GetManyRequest("meeting", meeting_ids, ["locked_from_inside"])],
                    lock_result=False,
                )
                .get("meeting", {})
                .items()
                if meeting.get("locked_from_inside")
            ]
            if len(locked_meetings):
                raise ActionException(
                    f"Cannot assign meetings because some selected meetings are locked: {', '.join(locked_meetings)}."
                )

    def create_action_result_element(
        self, instance: dict[str, Any]
    ) -> ActionResultElement | None:
        result = {}
        result["succeeded"] = list(self.success)
        result["standard_group"] = list(self.standard_meeting_ids)
        result["nothing"] = list(self.nothing_meeting_ids)
        return result
