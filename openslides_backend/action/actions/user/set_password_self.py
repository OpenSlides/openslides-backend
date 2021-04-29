from typing import Any, Dict

from openslides_backend.permissions.permission_helper import has_perm, is_temporary
from openslides_backend.permissions.permissions import Permissions

from ....models.models import User
from ....shared.exceptions import ActionException, PermissionDenied
from ....shared.patterns import FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("user.set_password_self")
class UserSetPasswordSelf(UpdateAction):
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

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        old_pw = instance.pop("old_password")
        new_pw = instance.pop("new_password")

        db_instance = self.datastore.get(
            FullQualifiedId(self.model.collection, self.user_id), ["password"]
        )

        if not self.auth.is_equals(old_pw, db_instance["password"]):
            raise ActionException("Wrong password")

        instance["password"] = self.auth.hash(new_pw)
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if self.auth.is_anonymous(self.user_id):
            raise ActionException("Can't set password for anonymous")

        instance["id"] = self.user_id
        if is_temporary(self.datastore, instance):
            if has_perm(
                self.datastore,
                self.user_id,
                Permissions.User.CAN_CHANGE_OWN_PASSWORD,
                instance["meeting_id"],
            ):
                return
            msg = f"You are not allowed to perform action {self.name}."
            msg += f" Missing permission: {Permissions.User.CAN_CHANGE_OWN_PASSWORD}"
            raise PermissionDenied(msg)
