from typing import Any
from collections.abc import Callable

from openslides_backend.services.database.commands import GetManyRequest
from openslides_backend.shared.exceptions import ActionException

from ....action.action import original_instances
from ....action.util.typing import ActionData
from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator, Or
from ....shared.mixins.user_scope_mixin import UserScopeMixin
from ...mixins.idp_mixin import IDPMixin
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .user_mixins import AdminIntegrityCheckMixin


@register_action("user.delete")
class UserDelete(
    UserScopeMixin,
    DeleteAction,
    AdminIntegrityCheckMixin,
    IDPMixin,
):
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

        try:
            self.user_id_to_idp_id[instance["id"]] = self.datastore.get(
                fqid=f"user/{instance.get('id')}",
                mapped_fields=["idp_id"]
                )["idp_id"]
        except Exception as e:
            self.logger.error(f"User {instance.get('id')} has no IDP ID: {e}")

        return super().update_instance(instance)

    def get_on_success(self, action_data: ActionData) -> Callable[[], None] | None:
        def on_success() -> None:
            if not action_data[0].get('id') in self.user_id_to_idp_id:
                self.logger.error(f"IDP ID for User {action_data[0].get('id')} not found, can't delete IDP user")
                return

            # Delete IDP account
            self.delete_user(self.user_id_to_idp_id[action_data[0].get('id')])

        return on_success

    def check_permissions(self, instance: dict[str, Any]) -> None:
        self.check_permissions_for_scope(instance["id"])

    def get_removed_meeting_id(self, instance: dict[str, Any]) -> int | None:
        return 0

    @original_instances
    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        self.check_meeting_admin_integrity(
            [user_id for date in action_data if (user_id := date.get("id"))]
        )
        self.user_id_to_idp_id: dict[int, str] = {}
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
        meetings = self.get_meeting_data_from_meeting_ids(list(meeting_ids_to_user_ids))
        self.filter_templates_from_meetings_data_dict(meeting_ids_to_user_ids, meetings)
        if not len(meeting_ids_to_user_ids):
            return
        self.check_admin_group_integrity(
            Or(*[FilterOperator("user_id", "=", user_id) for user_id in delete_data]),
            [
                admin_group_id
                for meeting in meetings.values()
                if (admin_group_id := meeting.get("admin_group_id"))
            ],
        )
