from ....models.models import Vote
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


# TODO should be internal
@register_action("vote.create")
class VoteCreate(CreateAction):
    """
    Internal action to create a vote.
    """

    model = Vote()
    schema = DefaultSchema(Vote()).get_create_schema(
        required_properties=["weight", "value", "option_id", "meeting_id"]
    )
