from typing import Any, Dict

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create_update_permissions_mixin import CreateUpdatePermissionsMixin
from .user_mixin import UserMixin


@register_action("user.update")
class UserUpdate(
    UserMixin,
    CreateUpdatePermissionsMixin,
    UpdateAction,
):
    """
    Action to update a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        optional_properties=[
            "username",
            "title",
            "first_name",
            "last_name",
            "is_active",
            "is_physical_person",
            "default_password",
            "can_change_own_password",
            "gender",
            "email",
            "default_number",
            "default_structure_level",
            "default_vote_weight",
            "organization_management_level",
            "committee_ids",
            "committee_$_management_level",
            "number_$",
            "structure_level_$",
            "vote_weight_$",
            "about_me_$",
            "comment_$",
            "vote_delegated_$_to_id",
            "vote_delegations_$_from_ids",
            "group_$_ids",
            "is_demo_user",
        ],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """Check, if user is in committee, where he wants to gain cml-permissions"""
        if instance.get("committee_$_management_level"):
            # get all committee_ids, where the cml-permission should be set
            committee_ids = {
                pair[0]
                for pair in instance.get("committee_$_management_level", {}).items()
                if pair[1]
            }
            if diff := committee_ids - set(instance.get("committee_ids", [])):
                user = self.datastore.get(
                    FullQualifiedId(Collection("user"), instance["id"]),
                    [
                        "committee_ids",
                    ],
                )
                if diff := diff - set(user.get("committee_ids", [])):
                    raise ActionException(
                        f"You must add the user to the committee(s) '{', '.join(tuple(map(str, diff)))}', because you want to give him committee management level permissions."
                    )

        return super().update_instance(instance)
