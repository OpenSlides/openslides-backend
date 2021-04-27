from ....models.models import Vote
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("vote.create", internal=True)
class VoteCreate(CreateAction):
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
            "meeting_id",
        ],
        optional_properties=["delegated_user_id", "user_id"],
    )
