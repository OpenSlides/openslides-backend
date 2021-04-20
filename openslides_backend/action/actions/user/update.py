from ....models.models import User
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryNoForInstanceMixin
from .create_update_permissions_mixin import CreateUpdatePermissionsMixin
from .user_mixin import UserMixin


@register_action("user.update")
class UserUpdate(
    CheckTemporaryNoForInstanceMixin,
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
            "gender",
            "email",
            "default_number",
            "default_structure_level",
            "default_vote_weight",
            "organisation_management_level",
            "committee_as_member_ids",
            "committee_as_manager_ids",
            "guest_meeting_ids",
            "number_$",
            "structure_level_$",
            "vote_weight_$",
            "about_me_$",
            "comment_$",
            "vote_delegated_$_to_id",
            "vote_delegations_$_from_ids",
            "group_$_ids",
        ],
    )
