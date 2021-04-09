from typing import Any, Dict

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryNoForInstanceMixin
from .user_mixin import UserMixin


@register_action("user.update")
class UserUpdate(CheckTemporaryNoForInstanceMixin, UpdateAction, UserMixin):
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
            "gender",
            "email",
            "default_number",
            "default_structure_level",
            "default_vote_weight",
            "organisation_management_level",
            "is_present_in_meeting_ids",
            "guest_meeting_ids",
            "committee_as_member_ids",
            "committee_as_manager_ids",
            "group_$_ids",
            "vote_delegations_$_from_ids",
            "vote_delegated_$_to_id",
            "comment_$",
            "number_$",
            "structure_level_$",
            "about_me_$",
            "vote_weight_$",
        ],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if instance.get("meeting_id") or self.datastore.get(
            FullQualifiedId(Collection("user"), instance["id"]), ["meeting_id"]
        ).get("meeting_id"):
            raise ActionException(
                "Please use Action user.update_temporary for temporary user"
            )
        return super().update_instance(instance)
