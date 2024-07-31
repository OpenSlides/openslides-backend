from typing import Any

from openslides_backend.services.datastore.commands import GetManyRequest

from ....action.action import original_instances
from ....action.util.typing import ActionData
from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator, Or
from ....shared.mixins.user_scope_mixin import UserScopeMixin
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("user.delete")
class UserDelete(UserScopeMixin, DeleteAction):
    """
    Action to delete a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_delete_schema()
    skip_archived_meeting_check = True
    history_information = "Account deleted"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        if instance["id"] == self.user_id:
            raise ActionException("You cannot delete yourself.")
        return super().update_instance(instance)

    def check_permissions(self, instance: dict[str, Any]) -> None:
        self.check_permissions_for_scope(instance["id"])

    def get_removed_meeting_id(self, instance: dict[str, Any]) -> int | None:
        return 0

    @original_instances
    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        self.check_meeting_admin_integrity(
            [user_id for date in action_data if (user_id := date.get("id"))]
        )
        return super().get_updated_instances(action_data)

    def check_meeting_admin_integrity(self, delete_data: list[int] = []) -> None:
        if not len(delete_data):
            return
        meeting_ids_to_user_ids: dict[int, list[int]] = {}
        users = self.datastore.get_many(
            [GetManyRequest("user", delete_data, ["meeting_ids", "meeting_user_ids"])]
        )["user"]
        for id_, user in users.items():
            for meeting_id in user.get("meeting_ids", []):
                if meeting_id not in meeting_ids_to_user_ids:
                    meeting_ids_to_user_ids[meeting_id] = [id_]
                else:
                    meeting_ids_to_user_ids[meeting_id].append(id_)
        if len(meeting_ids_to_user_ids):
            meetings = self.datastore.get_many(
                [
                    GetManyRequest(
                        "meeting",
                        list(meeting_ids_to_user_ids.keys()),
                        ["admin_group_id", "template_for_organization_id"],
                    )
                ]
            )["meeting"]
            for meeting_id, meeting in meetings.items():
                if meeting.get("template_for_organization_id"):
                    del meeting_ids_to_user_ids[meeting_id]
            if not len(meeting_ids_to_user_ids):
                return
            meeting_users = self.datastore.filter(
                "meeting_user",
                Or(
                    *[
                        FilterOperator("user_id", "=", user_id)
                        for user_id in delete_data
                    ]
                ),
                ["group_ids", "user_id"],
            )
            groups = self.datastore.get_many(
                [
                    GetManyRequest(
                        "group",
                        [
                            admin_group_id
                            for meeting in meetings.values()
                            if (admin_group_id := meeting.get("admin_group_id"))
                        ],
                        ["meeting_user_ids", "admin_group_for_meeting_id"],
                    )
                ]
            )["group"]
            broken_meetings: list[str] = []
            for group_data in groups.values():
                if group_data.get("meeting_user_ids") and not any(
                    m_user_id not in meeting_users
                    for m_user_id in group_data.get("meeting_user_ids", [])
                ):
                    broken_meetings.append(
                        str(group_data["admin_group_for_meeting_id"])
                    )
            if len(broken_meetings):
                raise ActionException(
                    f"Cannot remove last admin from meeting(s) {', '.join(sorted(broken_meetings))}"
                )
