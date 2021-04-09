from typing import Any, Dict

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .user_mixin import UserMixin


@register_action("user.update_self")
class UserUpdateSelf(UpdateAction, UserMixin):
    """
    Action to self update a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_default_schema(
        optional_properties=["username", "email", "about_me_$"]
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set id = user_id.
        """
        instance["id"] = self.user_id
        instance = super().update_instance(instance)

        if "about_me_$" in instance:
            meeting_id_str = str(
                self.datastore.get(
                    FullQualifiedId(Collection("user"), self.user_id), ["meeting_id"]
                ).get("meeting_id")
            )
            if meeting_id_str:
                diff = [
                    meeting
                    for meeting in instance["about_me_$"].keys()
                    if meeting != meeting_id_str
                ]
                if diff:
                    raise ActionException(
                        f"Temporary user may update about_me_$ only in his meeting, but tries in {diff}."
                    )
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if self.auth.is_anonymous(self.user_id):
            raise ActionException("Can't update for anonymous")
