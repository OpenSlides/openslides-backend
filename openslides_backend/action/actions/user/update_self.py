from typing import Any

from ....models.models import MeetingUser, User
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException, MissingPermission
from ...generics.update import UpdateAction
from ...mixins.meeting_user_helper import get_meeting_user
from ...mixins.send_email_mixin import EmailCheckMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .user_mixins import UpdateHistoryMixin, UserMixin, check_gender_exists


@register_action("user.update_self")
class UserUpdateSelf(EmailCheckMixin, UpdateAction, UserMixin, UpdateHistoryMixin):
    """
    Action to self update a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_default_schema(
        optional_properties=["username", "pronoun", "gender_id", "email"],
        additional_optional_fields={
            **MeetingUser().get_properties(
                "meeting_id", "vote_delegated_to_id", "vote_delegations_from_ids"
            )
        },
    )
    check_email_field = "email"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Set id = user_id.
        """
        instance["id"] = self.user_id
        instance = super().update_instance(instance)
        check_gender_exists(self.datastore, instance)
        return instance

    def meeting_user_set_data(self, instance: dict[str, Any]) -> None:
        if (deleg := set(instance.get("vote_delegations_from_ids", []))) and len(
            deleg.difference(
                (
                    get_meeting_user(
                        self.datastore,
                        instance["meeting_id"],
                        instance["id"],
                        ["vote_delegations_from_ids"],
                    )
                    or {}
                ).get("vote_delegations_from_ids", [])
            )
        ):
            raise ActionException(
                "Can't add delegations from other people with user.update_self."
            )
        super().meeting_user_set_data(instance)

    def check_permissions(self, instance: dict[str, Any]) -> None:
        self.assert_not_anonymous()
        if (
            (meeting_id := instance.get("meeting_id"))
            and (
                "vote_delegated_to_id" in instance
                or "vote_delegations_from_ids" in instance
            )
            and not has_perm(
                self.datastore,
                self.user_id,
                Permissions.User.CAN_EDIT_OWN_DELEGATION,
                meeting_id,
            )
        ):
            raise MissingPermission(Permissions.User.CAN_EDIT_OWN_DELEGATION)
