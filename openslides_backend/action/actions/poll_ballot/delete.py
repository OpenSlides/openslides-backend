from ....models.models import PollBallot
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("poll_ballot.delete", action_type=ActionType.BACKEND_INTERNAL)
class PollBallotDelete(DeleteAction):
    """
    Action to delete a poll_ballot.
    """

    model = PollBallot()
    schema = DefaultSchema(PollBallot()).get_delete_schema()
