from typing import Any

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.exceptions import ActionException
from ....shared.schema import id_list_schema, optional_id_schema
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ....services.datastore.commands import GetManyRequest


@register_action("user.merge_together")
class UserMergeTogether(CreateAction, CheckForArchivedMeetingMixin):
    """
    Action to merge users together.
    """

    model = User()
    schema = DefaultSchema(User()).get_default_schema(
        required_properties=[
            "username",
        ],
        optional_properties=[
            "title",
            "first_name",
            "last_name",
            "is_active",
            "is_physical_person",
            "default_password",
            "gender",
            "email",
            "default_vote_weight",
        ],
        additional_required_fields={
            "user_ids": {
                "description": "A list of user ids to merge into a user.",
                **id_list_schema,
            }
        },
        additional_optional_fields={
            "password_from_user_id": {
                "description": "The password hash from this user is copied. The user id must be given in user_ids! If it is empty, the default password is used.",
                **optional_id_schema,
            }
        },
    )
    permission = permission = OrganizationManagementLevel.CAN_MANAGE_USERS

    def prefetch(self, action_data: ActionData) -> None:
        user_ids = [
            id_
            for instance in action_data
            for id_ in set(instance.get("user_ids", []))
        ]
        if len(user_ids) != len(set(user_ids)):
            raise ActionException("Cannot merge one user into multiple final users")
        users = self.datastore.get_many(
            [
                GetManyRequest(
                    "user",
                    user_ids,
                    [],
                )
            ]
        )["user"]
        self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting_user",
                    list(
                        {
                            id_
                            for user in users.values()
                            for id_ in user.get("meeting_user_ids", [])
                        }
                    ),
                    [],
                )
            ]
        )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        raise ActionException(
            "This action is still not implemented, but permission checked"
        )
        return instance
