from ....models.models import Vote
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("vote.create", action_type=ActionType.BACKEND_INTERNAL)
class VoteCreate(CreateActionWithInferredMeeting):
    """
    Internal action to create a vote.
    """

    model = Vote()
    schema = DefaultSchema(Vote()).get_create_schema(
        required_properties=[
            "weight",
            "value",
            "option_id",
            "user_token",
        ],
        optional_properties=["delegated_user_id", "user_id"],
    )

    relation_field_for_meeting = "option_id"
