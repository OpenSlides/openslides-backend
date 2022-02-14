from typing import Any, Dict

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.patterns import FullQualifiedId
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
        optional_properties=["username", "pronoun", "gender", "email", "about_me_$"]
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set id = user_id.
        """
        instance["id"] = self.user_id
        instance = super().update_instance(instance)

        if "about_me_$" in instance:
            user = self.datastore.get(
                FullQualifiedId(self.model.collection, self.user_id), ["meeting_ids"]
            )

            not_supported_meetings = [
                meeting
                for meeting in [int(key) for key in instance["about_me_$"].keys()]
                if meeting not in user.get("meeting_ids", [])
            ]
            if not_supported_meetings:
                raise ActionException(
                    f"User may update about_me_$ only in his meetings, but tries in {not_supported_meetings}"
                )
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        self.assert_not_anonymous()
