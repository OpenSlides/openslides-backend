from ....models.models import User
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("user.update")
class UserUpdate(UpdateAction):
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
            "comment_$",
            "number_$",
            "structure_level_$",
            "about_me_$",
            "vote_weight_$",
        ],
    )
