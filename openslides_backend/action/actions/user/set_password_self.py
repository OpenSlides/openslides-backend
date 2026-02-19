from typing import Any

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import User
from ....shared.exceptions import ActionException, PermissionDenied
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .keycloak_sync_mixin import KeycloakPasswordSyncMixin
from .password_mixins import ClearSessionsMixin


@register_action("user.set_password_self")
class UserSetPasswordSelf(
    KeycloakPasswordSyncMixin,
    UpdateAction,
    CheckForArchivedMeetingMixin,
    ClearSessionsMixin,
):
    """
    Action to update the own password.
    """

    model = User()
    schema = DefaultSchema(User()).get_default_schema(
        additional_required_fields={
            "old_password": {"type": "string", "minLength": 1},
            "new_password": {"type": "string", "minLength": 1},
        }
    )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        old_pw = instance.pop("old_password")
        new_pw = instance.pop("new_password")

        db_instance = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, self.user_id),
            ["password", "saml_id"],
            lock_result=False,
        )
        if db_instance.get("saml_id"):
            raise ActionException(
                f"user {db_instance['saml_id']} is a Single Sign On user and has no local OpenSlides password."
            )
        if not self.auth.is_equal(old_pw, db_instance["password"]):
            raise ActionException("Wrong password")

        instance["password"] = self.auth.hash(new_pw)
        self._sync_password_to_keycloak(instance, new_pw)
        return instance

    def check_permissions(self, instance: dict[str, Any]) -> None:
        self.assert_not_anonymous()
        instance["id"] = self.user_id
        user = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, self.user_id),
            ["can_change_own_password"],
            lock_result=False,
        )
        if not user.get("can_change_own_password"):
            raise PermissionDenied("You cannot change your password.")
