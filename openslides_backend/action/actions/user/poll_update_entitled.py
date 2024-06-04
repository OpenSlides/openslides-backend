from ....models.models import Poll
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("poll.update_entitled", action_type=ActionType.BACKEND_INTERNAL)
class PollUpdateEntitledAction(UpdateAction):
    """
    Action to update a polls entitled users. Should only be used by the user merge.
    """

    internal_fields = [
        "entitled_users_at_stop",
    ]

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema(
        required_properties=["entitled_users_at_stop"]
    )
    permission = permission = OrganizationManagementLevel.CAN_MANAGE_USERS
